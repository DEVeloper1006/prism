"""Track 3: Technical Quality Scoring — Laplacian, histogram, optical flow."""

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger("[PIPELINE:T3]")


class TechnicalTrack:
    def __init__(self) -> None:
        pass

    async def process(self, video_path: Path) -> dict:
        logger.info("Processing technical track for %s", video_path.name)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.warning("Cannot open video: %s", video_path.name)
            return {}

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        sample_interval = max(int(fps), 1)

        sharpness_scores: list[float] = []
        exposure_scores: list[float] = []
        stability_scores: list[float] = []
        color_scores: list[float] = []
        prev_gray = None

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                sharpness_scores.append(self._score_sharpness(gray))
                exposure_scores.append(self._score_exposure(gray))

                if prev_gray is not None:
                    stability_scores.append(self._score_stability(prev_gray, gray))

                color_scores.append(self._score_color_consistency(frame))
                prev_gray = gray

            frame_idx += 1

        cap.release()

        return {
            "sharpness_score": self._median_clamp(sharpness_scores),
            "exposure_score": self._median_clamp(exposure_scores),
            "stability_score": self._median_clamp(stability_scores) if stability_scores else 50,
            "color_score": self._median_clamp(color_scores),
        }

    def _score_sharpness(self, gray: np.ndarray) -> float:
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        variance = lap.var()
        return min(100.0, variance / 5.0)

    def _score_exposure(self, gray: np.ndarray) -> float:
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()
        spread = np.std(np.arange(256) * hist) * 2
        mean_brightness = np.mean(gray)
        center_penalty = 1.0 - abs(mean_brightness - 128) / 128.0
        return min(100.0, spread * center_penalty * 1.5)

    def _score_stability(self, prev: np.ndarray, curr: np.ndarray) -> float:
        flow = cv2.calcOpticalFlowFarneback(
            prev, curr, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
        mean_motion = np.mean(magnitude)
        return max(0.0, min(100.0, 100.0 - mean_motion * 10))

    def _score_color_consistency(self, frame: np.ndarray) -> float:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h_std = np.std(hsv[:, :, 0].astype(float))
        s_std = np.std(hsv[:, :, 1].astype(float))
        consistency = max(0.0, 100.0 - (h_std + s_std) / 2)
        return min(100.0, consistency)

    def _median_clamp(self, scores: list[float]) -> int:
        if not scores:
            return 50
        return max(0, min(100, int(np.median(scores))))

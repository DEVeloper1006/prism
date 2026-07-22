"""Track 4: Face Intelligence — face_recognition + DBSCAN clustering."""

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger("[PIPELINE:T4]")


class FaceTrack:
    def __init__(self, prism_dir: Path | None = None) -> None:
        self.prism_dir = prism_dir

    async def process(self, video_path: Path, keyframe_paths: list[Path] | None = None) -> dict:
        logger.info("Processing face track for %s", video_path.name)

        try:
            import face_recognition as fr
        except ImportError:
            logger.warning("face_recognition not available; face detection disabled")
            return {"faces": []}

        if not keyframe_paths:
            keyframe_paths = self._extract_sample_frames(video_path)

        all_encodings: list[np.ndarray] = []
        all_locations: list[dict] = []

        for kf_path in keyframe_paths:
            frame = cv2.imread(str(kf_path))
            if frame is None:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = fr.face_locations(rgb)
            encodings = fr.face_encodings(rgb, locations)

            h, w = frame.shape[:2]
            for loc, enc in zip(locations, encodings):
                top, right, bottom, left = loc
                all_encodings.append(enc)
                all_locations.append({
                    "keyframe": str(kf_path),
                    "bbox_x": left,
                    "bbox_y": top,
                    "bbox_w": right - left,
                    "bbox_h": bottom - top,
                    "timestamp_seconds": 0.0,
                })

                if self.prism_dir:
                    face_crop = frame[top:bottom, left:right]
                    if face_crop.size > 0:
                        faces_dir = self.prism_dir / "faces" / "unclustered"
                        faces_dir.mkdir(parents=True, exist_ok=True)
                        crop_path = faces_dir / f"{video_path.stem}_{len(all_encodings):03d}.jpg"
                        cv2.imwrite(str(crop_path), face_crop, [cv2.IMWRITE_JPEG_QUALITY, 85])

        return {
            "faces": [
                {**loc, "encoding": enc.tolist()}
                for loc, enc in zip(all_locations, all_encodings)
            ],
        }

    def _extract_sample_frames(self, video_path: Path) -> list[Path]:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_interval = max(int(fps * 2), 1)

        frames: list[Path] = []
        if not self.prism_dir:
            cap.release()
            return frames

        tmp_dir = self.prism_dir / "faces" / "tmp_frames"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        frame_idx = 0
        while frame_idx < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
            path = tmp_dir / f"{video_path.stem}_{frame_idx:06d}.jpg"
            cv2.imwrite(str(path), frame)
            frames.append(path)
            frame_idx += sample_interval

        cap.release()
        return frames[:20]

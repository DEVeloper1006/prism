"""Track 1: Visual Intelligence — PySceneDetect + OpenCLIP + VLM."""

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger("[PIPELINE:T1]")


class ClipEncoder:
    """OpenCLIP ViT-L/14 encoder for text and image embeddings."""

    def __init__(self) -> None:
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self._load()

    def _load(self) -> None:
        try:
            import open_clip
            import torch

            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                "ViT-L-14", pretrained="datacomp_xl_s13b_b90k"
            )
            self.tokenizer = open_clip.get_tokenizer("ViT-L-14")
            self.model.eval()
            self.device = "mps" if torch.backends.mps.is_available() else "cpu"
            self.model = self.model.to(self.device)
            logger.info("OpenCLIP ViT-L/14 loaded on %s", self.device)
        except Exception:
            logger.warning("OpenCLIP not available; CLIP features disabled")
            self.model = None

    def encode_image(self, image: np.ndarray) -> list[float] | None:
        if self.model is None:
            return None
        try:
            import torch
            from PIL import Image

            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            img_tensor = self.preprocess(pil_img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                embedding = self.model.encode_image(img_tensor)
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
            return embedding.cpu().squeeze().tolist()
        except Exception:
            logger.exception("CLIP encode_image failed")
            return None

    def encode_text(self, text: str) -> list[float] | None:
        if self.model is None:
            return None
        try:
            import torch

            tokens = self.tokenizer([text]).to(self.device)
            with torch.no_grad():
                embedding = self.model.encode_text(tokens)
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
            return embedding.cpu().squeeze().tolist()
        except Exception:
            logger.exception("CLIP encode_text failed")
            return None


class VisualTrack:
    def __init__(self, clip_encoder: ClipEncoder | None = None, prism_dir: Path | None = None) -> None:
        self.clip_encoder = clip_encoder
        self.prism_dir = prism_dir

    async def process(self, video_path: Path) -> dict:
        logger.info("Processing visual track for %s", video_path.name)

        keyframes = self._extract_keyframes(video_path)
        embeddings: list[list[float]] = []
        caption = None
        shot_type = "establishing"

        for kf_path in keyframes:
            frame = cv2.imread(str(kf_path))
            if frame is None:
                continue

            if self.clip_encoder:
                emb = self.clip_encoder.encode_image(frame)
                if emb:
                    embeddings.append(emb)

            if caption is None:
                caption = self._generate_caption(kf_path)

            st = self._classify_shot_type(frame)
            if st != "establishing":
                shot_type = st

        avg_embedding = None
        if embeddings:
            avg = np.mean(embeddings, axis=0)
            avg_embedding = (avg / np.linalg.norm(avg)).tolist()

        return {
            "keyframes": [str(p) for p in keyframes],
            "embedding": avg_embedding,
            "scene_caption": caption,
            "shot_type": shot_type,
        }

    def _extract_keyframes(self, video_path: Path) -> list[Path]:
        if not self.prism_dir:
            return []

        keyframe_dir = self.prism_dir / "keyframes" / video_path.stem
        keyframe_dir.mkdir(parents=True, exist_ok=True)

        try:
            from scenedetect import SceneManager, open_video
            from scenedetect.detectors import ContentDetector

            video = open_video(str(video_path))
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=27.0))
            scene_manager.detect_scenes(video)
            scene_list = scene_manager.get_scene_list()

            cap = cv2.VideoCapture(str(video_path))
            keyframes: list[Path] = []

            if not scene_list:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if ret:
                    path = keyframe_dir / "kf_000.jpg"
                    cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    keyframes.append(path)
            else:
                for i, (start, _end) in enumerate(scene_list):
                    frame_num = start.get_frames()
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                    ret, frame = cap.read()
                    if ret:
                        path = keyframe_dir / f"kf_{i:03d}.jpg"
                        cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                        keyframes.append(path)

            cap.release()
            return keyframes

        except ImportError:
            logger.warning("PySceneDetect not available; extracting first frame only")
            return self._extract_first_frame(video_path, keyframe_dir)

    def _extract_first_frame(self, video_path: Path, keyframe_dir: Path) -> list[Path]:
        cap = cv2.VideoCapture(str(video_path))
        ret, frame = cap.read()
        cap.release()
        if ret:
            path = keyframe_dir / "kf_000.jpg"
            cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return [path]
        return []

    def _generate_caption(self, keyframe_path: Path) -> str | None:
        try:
            import httpx

            with open(keyframe_path, "rb") as f:
                import base64
                img_b64 = base64.b64encode(f.read()).decode()

            resp = httpx.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llava",
                    "prompt": "Describe this scene from a film shoot in one sentence. Focus on what is visible: subjects, setting, lighting, and framing.",
                    "images": [img_b64],
                    "stream": False,
                },
                timeout=30.0,
            )
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
        except Exception:
            logger.debug("VLM caption generation unavailable")
        return None

    def _classify_shot_type(self, frame: np.ndarray) -> str:
        try:
            import face_recognition as fr

            locations = fr.face_locations(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if not locations:
                return "establishing"

            h, w = frame.shape[:2]
            frame_area = h * w
            largest_face_area = max(
                (bottom - top) * (right - left)
                for top, right, bottom, left in locations
            )
            ratio = largest_face_area / frame_area

            if ratio > 0.40:
                return "close-up"
            elif ratio > 0.15:
                return "medium"
            else:
                return "wide"
        except ImportError:
            return "establishing"

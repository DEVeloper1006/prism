"""Job queue, worker pool, and progress event bus for the ingestion pipeline."""

import asyncio
import hashlib
import json
import logging
import uuid
from pathlib import Path

from pipeline.audio import AudioTrack
from pipeline.color_palette import ColorPaletteExtractor
from pipeline.faces import FaceTrack
from pipeline.metadata import MetadataTrack
from pipeline.scanner import FileScanner
from pipeline.technical import TechnicalTrack
from pipeline.visual import ClipEncoder, VisualTrack

logger = logging.getLogger("[PIPELINE:ORCHESTRATOR]")


class PipelineOrchestrator:
    def __init__(
        self,
        media_root: Path,
        metadata_store,  # noqa: ANN001
        vector_store,  # noqa: ANN001
        ws_manager=None,  # noqa: ANN001
    ) -> None:
        self.media_root = media_root
        self.metadata_store = metadata_store
        self.vector_store = vector_store
        self.ws_manager = ws_manager
        self.scanner = FileScanner(media_root)
        self.prism_dir = media_root / ".prism"

        self.clip_encoder: ClipEncoder | None = None
        self.visual = VisualTrack(prism_dir=self.prism_dir)
        self.audio = AudioTrack(prism_dir=self.prism_dir)
        self.technical = TechnicalTrack()
        self.faces = FaceTrack(prism_dir=self.prism_dir)
        self.metadata_track = MetadataTrack()
        self.color_extractor = ColorPaletteExtractor()

        self._cancelled = False
        self._running = False
        self.total_files = 0
        self.processed_files = 0
        self.status = "idle"

    def load_models(self) -> None:
        try:
            self.clip_encoder = ClipEncoder()
            self.visual = VisualTrack(clip_encoder=self.clip_encoder, prism_dir=self.prism_dir)
        except Exception:
            logger.warning("CLIP encoder failed to load; semantic search disabled")

    async def ingest(self, folder: Path) -> dict:
        logger.info("Starting ingestion for %s", folder)
        self._cancelled = False
        self._running = True
        self.status = "running"

        self.scanner.ensure_sidecar_dirs()
        files = self.scanner.scan()
        self.total_files = len(files)
        self.processed_files = 0

        await self._broadcast({
            "type": "ingest_start",
            "total_files": self.total_files,
            "folder": str(folder),
        })

        for video_path in files:
            if self._cancelled:
                self.status = "cancelled"
                break

            clip_id = self._make_clip_id(video_path)
            await self._process_clip(clip_id, video_path)
            self.processed_files += 1

            await self._broadcast({
                "type": "clip_complete",
                "clip_id": clip_id,
                "progress": self.processed_files / max(self.total_files, 1),
                "processed": self.processed_files,
                "total": self.total_files,
            })

        self._running = False
        if not self._cancelled:
            self.status = "completed"

        await self._broadcast({
            "type": "ingest_complete",
            "status": self.status,
            "total_processed": self.processed_files,
        })

        self.metadata_store.log_action("ingest", json.dumps({
            "folder": str(folder),
            "total": self.total_files,
            "processed": self.processed_files,
            "status": self.status,
        }))

        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "status": self.status,
        }

    async def _process_clip(self, clip_id: str, video_path: Path) -> None:
        logger.info("Processing %s (%s)", video_path.name, clip_id)
        file_hash = hashlib.sha256(video_path.read_bytes()).hexdigest()

        clip_data: dict = {"id": clip_id, "file_hash": file_hash}

        tracks = {
            "T5:metadata": self.metadata_track.process(video_path),
            "T3:technical": self.technical.process(video_path),
            "T1:visual": self.visual.process(video_path),
            "T2:audio": self.audio.process(video_path),
        }

        for track_name, coro in tracks.items():
            await self._broadcast({
                "type": "track_start",
                "clip_id": clip_id,
                "track": track_name,
            })
            try:
                result = await coro
                self._merge_track_result(clip_data, track_name, result)
            except Exception:
                logger.exception("Track %s failed for %s", track_name, video_path.name)
            await self._broadcast({
                "type": "track_complete",
                "clip_id": clip_id,
                "track": track_name,
            })

        keyframe_paths = [Path(p) for p in clip_data.get("_keyframes", [])]
        if keyframe_paths:
            await self._broadcast({"type": "track_start", "clip_id": clip_id, "track": "T4:faces"})
            try:
                face_result = await self.faces.process(video_path, keyframe_paths)
                self._store_faces(clip_id, face_result)
            except Exception:
                logger.exception("Face track failed for %s", video_path.name)
            await self._broadcast({"type": "track_complete", "clip_id": clip_id, "track": "T4:faces"})

            colors = self.color_extractor.extract(keyframe_paths)
            if colors:
                clip_data["dominant_colors"] = json.dumps(colors)
                self.color_extractor.save(clip_id, colors, self.prism_dir)

        embedding = clip_data.pop("_embedding", None)
        clip_data.pop("_keyframes", None)

        self._generate_thumbnail(video_path, clip_id)

        self.metadata_store.insert_clip(clip_data)

        if embedding:
            self.vector_store.add(clip_id, embedding, {"shot_type": clip_data.get("shot_type", "")})

        transcript_segments = clip_data.pop("_transcript", [])
        for seg in transcript_segments:
            seg["clip_id"] = clip_id
            self.metadata_store.insert_transcript_segment(seg)

        audio_events = clip_data.pop("_audio_events", [])
        for evt in audio_events:
            evt["clip_id"] = clip_id
            self.metadata_store.insert_audio_event(evt)

    def _merge_track_result(self, clip_data: dict, track_name: str, result: dict) -> None:
        if "T5" in track_name:
            for key in ["file_path", "file_size_bytes", "created_at", "duration_seconds",
                        "resolution", "fps", "codec", "color_space", "audio_channels", "camera"]:
                if key in result:
                    clip_data[key] = result[key]

        elif "T3" in track_name:
            for key in ["sharpness_score", "exposure_score", "stability_score", "color_score"]:
                if key in result:
                    clip_data[key] = result[key]

        elif "T1" in track_name:
            clip_data["scene_caption"] = result.get("scene_caption")
            clip_data["shot_type"] = result.get("shot_type")
            if result.get("embedding"):
                clip_data["_embedding"] = result["embedding"]
            if result.get("keyframes"):
                clip_data["_keyframes"] = result["keyframes"]

        elif "T2" in track_name:
            clip_data["audio_quality"] = result.get("audio_quality")
            clip_data["has_dialogue"] = result.get("has_dialogue", False)
            clip_data["_transcript"] = result.get("transcript", [])
            clip_data["_audio_events"] = result.get("audio_events", [])

    def _store_faces(self, clip_id: str, face_result: dict) -> None:
        for face in face_result.get("faces", []):
            cluster_id = self.metadata_store.insert_face_cluster(
                label=None,
                encoding=None,
                rep_path=face.get("keyframe"),
            )
            self.metadata_store.insert_face_appearance({
                "cluster_id": cluster_id,
                "clip_id": clip_id,
                "timestamp_seconds": face.get("timestamp_seconds", 0),
                "bbox_x": face["bbox_x"],
                "bbox_y": face["bbox_y"],
                "bbox_w": face["bbox_w"],
                "bbox_h": face["bbox_h"],
                "confidence": 1.0,
            })

    def _generate_thumbnail(self, video_path: Path, clip_id: str) -> None:
        thumb_dir = self.prism_dir / "thumbs"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = thumb_dir / f"{clip_id}.webp"

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps))
        ret, frame = cap.read()
        cap.release()

        if ret:
            h, w = frame.shape[:2]
            new_w = 320
            new_h = int(h * (new_w / w))
            thumb = cv2.resize(frame, (new_w, new_h))
            cv2.imwrite(str(thumb_path), thumb, [cv2.IMWRITE_WEBP_QUALITY, 80])

    def _make_clip_id(self, video_path: Path) -> str:
        return video_path.stem

    async def cancel(self) -> None:
        self._cancelled = True
        self.status = "cancelling"
        logger.info("Cancellation requested")

    def get_status(self) -> dict:
        return {
            "status": self.status,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "folder_path": str(self.media_root),
        }

    async def _broadcast(self, message: dict) -> None:
        if self.ws_manager:
            await self.ws_manager.broadcast(message)

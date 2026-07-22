"""Track 5: Metadata Extraction — ffprobe + ExifTool + filesystem."""

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("[PIPELINE:T5]")


class MetadataTrack:
    def __init__(self) -> None:
        pass

    async def process(self, video_path: Path) -> dict:
        logger.info("Processing metadata track for %s", video_path.name)

        result: dict = {
            "file_path": str(video_path),
            "file_size_bytes": video_path.stat().st_size,
            "created_at": datetime.fromtimestamp(
                video_path.stat().st_birthtime
                if hasattr(video_path.stat(), "st_birthtime")
                else video_path.stat().st_mtime,
                tz=timezone.utc,
            ).isoformat(),
        }

        probe = self._run_ffprobe(video_path)
        if probe:
            result.update(probe)

        return result

    def _run_ffprobe(self, video_path: Path) -> dict | None:
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(video_path),
            ]
            output = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
            )
            if output.returncode != 0:
                logger.warning("ffprobe failed for %s: %s", video_path.name, output.stderr)
                return None

            data = json.loads(output.stdout)
            return self._parse_ffprobe(data)
        except FileNotFoundError:
            logger.warning("ffprobe not found; install ffmpeg to enable metadata extraction")
            return None
        except Exception:
            logger.exception("ffprobe error for %s", video_path.name)
            return None

    def _parse_ffprobe(self, data: dict) -> dict:
        result: dict = {}
        fmt = data.get("format", {})

        result["duration_seconds"] = float(fmt.get("duration", 0))

        video_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
            None,
        )
        audio_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
            None,
        )

        if video_stream:
            w = video_stream.get("width", 0)
            h = video_stream.get("height", 0)
            result["resolution"] = f"{w}x{h}" if w and h else None
            result["codec"] = video_stream.get("codec_name")
            result["color_space"] = video_stream.get("color_space") or video_stream.get("pix_fmt")

            fps_str = video_stream.get("r_frame_rate", "0/1")
            if "/" in str(fps_str):
                num, den = fps_str.split("/")
                result["fps"] = round(float(num) / float(den), 2) if float(den) > 0 else None
            else:
                result["fps"] = float(fps_str)

        if audio_stream:
            result["audio_channels"] = int(audio_stream.get("channels", 0))

        tags = fmt.get("tags", {})
        if not tags:
            tags = (video_stream or {}).get("tags", {})

        result["camera"] = tags.get("make") or tags.get("com.apple.quicktime.make")
        model = tags.get("model") or tags.get("com.apple.quicktime.model")
        if model:
            result["camera"] = f"{result.get('camera', '')} {model}".strip() or model

        return result

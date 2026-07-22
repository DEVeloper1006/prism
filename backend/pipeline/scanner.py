"""File walker, checksum computation, and manifest diffing."""

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger("[PIPELINE:SCANNER]")

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".mxf", ".m4v",
    ".wmv", ".flv", ".webm", ".mpg", ".mpeg", ".m2ts",
    ".ts", ".3gp", ".r3d", ".braw", ".ari",
}


class FileScanner:
    def __init__(self, media_root: Path) -> None:
        self.media_root = media_root
        self.prism_dir = media_root / ".prism"
        self.manifest_path = self.prism_dir / "manifest.json"

    def scan(self) -> list[Path]:
        logger.info("Scanning %s", self.media_root)
        manifest = self._load_manifest()

        new_files: list[Path] = []
        current_hashes: dict[str, str] = {}

        for path in sorted(self.media_root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in VIDEO_EXTENSIONS:
                continue
            if ".prism" in path.parts:
                continue

            file_hash = self._compute_hash(path)
            rel_path = str(path.relative_to(self.media_root))
            current_hashes[rel_path] = file_hash

            if manifest.get(rel_path) != file_hash:
                new_files.append(path)
                logger.info("New/modified: %s", rel_path)

        self._save_manifest(current_hashes)
        logger.info("Scan complete: %d new/modified files out of %d total", len(new_files), len(current_hashes))
        return new_files

    def count_video_files(self) -> int:
        count = 0
        for path in self.media_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS and ".prism" not in path.parts:
                count += 1
        return count

    def _compute_hash(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def _load_manifest(self) -> dict[str, str]:
        if not self.manifest_path.exists():
            return {}
        with open(self.manifest_path) as f:
            return json.load(f)

    def _save_manifest(self, hashes: dict[str, str]) -> None:
        self.prism_dir.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w") as f:
            json.dump(hashes, f, indent=2)

    def ensure_sidecar_dirs(self) -> None:
        dirs = [
            "thumbs", "keyframes", "transcripts", "faces",
            "waveforms", "color_palettes", "storyboards",
            "luts", "exports", "chroma",
        ]
        for d in dirs:
            (self.prism_dir / d).mkdir(parents=True, exist_ok=True)

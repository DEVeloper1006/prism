"""Color palette extraction using k-means clustering on keyframe pixels."""

import json
import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger("[PIPELINE:COLOR]")


class ColorPaletteExtractor:
    def __init__(self, n_colors: int = 6) -> None:
        self.n_colors = n_colors

    def extract(self, keyframe_paths: list[Path]) -> list[str]:
        if not keyframe_paths:
            return []

        all_pixels: list[np.ndarray] = []
        for path in keyframe_paths[:3]:
            frame = cv2.imread(str(path))
            if frame is None:
                continue
            small = cv2.resize(frame, (64, 64))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            all_pixels.append(rgb.reshape(-1, 3).astype(np.float32))

        if not all_pixels:
            return []

        pixels = np.vstack(all_pixels)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, self.n_colors, None, criteria, 3, cv2.KMEANS_PP_CENTERS
        )

        counts = np.bincount(labels.flatten(), minlength=self.n_colors)
        sorted_indices = np.argsort(-counts)
        colors = centers[sorted_indices].astype(int)

        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors]
        return hex_colors

    def save(self, clip_id: str, colors: list[str], prism_dir: Path) -> None:
        palette_dir = prism_dir / "color_palettes"
        palette_dir.mkdir(parents=True, exist_ok=True)
        with open(palette_dir / f"{clip_id}.json", "w") as f:
            json.dump(colors, f)

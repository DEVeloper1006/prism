"""Generate sample clips with fake analysis data for UI development."""

import json
import random
import sys
from pathlib import Path


def generate_clip(index: int) -> dict:
    cameras = ["Sony A6700", "Canon R5", "Blackmagic 6K", "RED Komodo"]
    resolutions = ["1920x1080", "3840x2160", "4096x2160", "6144x3456"]
    codecs = ["H.264", "H.265", "ProRes 422", "BRAW"]

    return {
        "id": f"A{index:03d}_C{random.randint(1, 99):03d}",
        "file_path": f"footage/day{random.randint(1, 5)}/A{index:03d}_C{random.randint(1, 99):03d}.mp4",
        "file_hash": f"{random.getrandbits(256):064x}",
        "duration_seconds": round(random.uniform(3.0, 180.0), 1),
        "resolution": random.choice(resolutions),
        "fps": random.choice([23.976, 24.0, 25.0, 29.97, 30.0, 59.94, 60.0]),
        "codec": random.choice(codecs),
        "camera": random.choice(cameras),
        "has_dialogue": random.random() > 0.6,
        "sharpness_score": random.randint(20, 100),
        "exposure_score": random.randint(30, 100),
        "stability_score": random.randint(10, 100),
        "color_score": random.randint(40, 100),
        "scene_caption": random.choice([
            "Wide establishing shot of city skyline at sunset",
            "Close-up interview with subject, bookshelf background",
            "Handheld tracking shot through crowded market",
            "Aerial drone shot over coastal cliffs",
            "Locked-off shot of empty room, natural light",
            "Two-shot conversation at restaurant table",
        ]),
    }


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    clips = [generate_clip(i) for i in range(1, count + 1)]
    print(json.dumps(clips, indent=2))


if __name__ == "__main__":
    main()

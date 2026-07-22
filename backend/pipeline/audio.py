"""Track 2: Audio Intelligence — Whisper + pyannote + RMS analysis."""

import json
import logging
import subprocess
from pathlib import Path

import numpy as np

logger = logging.getLogger("[PIPELINE:T2]")


class AudioTrack:
    def __init__(self, prism_dir: Path | None = None) -> None:
        self.prism_dir = prism_dir

    async def process(self, video_path: Path) -> dict:
        logger.info("Processing audio track for %s", video_path.name)

        audio_path = self._extract_audio(video_path)
        if audio_path is None:
            return {"audio_quality": "no_audio", "has_dialogue": False}

        transcript = self._transcribe(audio_path, video_path.stem)
        quality = self._analyze_quality(audio_path)
        events = self._detect_events(audio_path)
        has_dialogue = len(transcript) > 0

        return {
            "transcript": transcript,
            "audio_quality": quality,
            "audio_events": events,
            "has_dialogue": has_dialogue,
        }

    def _extract_audio(self, video_path: Path) -> Path | None:
        if not self.prism_dir:
            return None
        audio_dir = self.prism_dir / "audio_tmp"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_dir / f"{video_path.stem}.wav"

        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(video_path),
                    "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                    str(audio_path),
                ],
                capture_output=True, timeout=120,
            )
            if audio_path.exists() and audio_path.stat().st_size > 0:
                return audio_path
        except FileNotFoundError:
            logger.warning("ffmpeg not found; audio extraction disabled")
        except Exception:
            logger.exception("Audio extraction failed for %s", video_path.name)
        return None

    def _transcribe(self, audio_path: Path, clip_stem: str) -> list[dict]:
        try:
            import whisper

            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path), word_timestamps=True)

            segments: list[dict] = []
            for seg in result.get("segments", []):
                segments.append({
                    "start_time": seg["start"],
                    "end_time": seg["end"],
                    "text": seg["text"].strip(),
                    "confidence": seg.get("avg_logprob", 0),
                })

            if self.prism_dir:
                transcript_dir = self.prism_dir / "transcripts"
                transcript_dir.mkdir(parents=True, exist_ok=True)
                with open(transcript_dir / f"{clip_stem}.json", "w") as f:
                    json.dump(segments, f, indent=2)

            return segments

        except ImportError:
            logger.warning("Whisper not available; transcription disabled")
            return []
        except Exception:
            logger.exception("Transcription failed for %s", audio_path.name)
            return []

    def _analyze_quality(self, audio_path: Path) -> str:
        try:
            import wave

            with wave.open(str(audio_path), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

            if len(samples) == 0:
                return "silent"

            rms = np.sqrt(np.mean(samples ** 2))
            peak = np.max(np.abs(samples))

            if peak > 32000:
                return "clipping"
            if rms < 200:
                return "low_level"
            if rms > 20000:
                return "hot"
            return "good"

        except Exception:
            return "unknown"

    def _detect_events(self, audio_path: Path) -> list[dict]:
        events: list[dict] = []
        try:
            import wave

            with wave.open(str(audio_path), "rb") as wf:
                sample_rate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())
                samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

            if len(samples) == 0:
                return events

            window_size = sample_rate
            for i in range(0, len(samples) - window_size, window_size):
                chunk = samples[i : i + window_size]
                rms = np.sqrt(np.mean(chunk ** 2))
                peak = np.max(np.abs(chunk))
                timestamp = i / sample_rate

                if rms < 100:
                    events.append({
                        "event_type": "silence",
                        "timestamp_seconds": timestamp,
                        "duration_seconds": 1.0,
                        "confidence": 0.9,
                    })
                elif peak > 28000 and rms < 5000:
                    events.append({
                        "event_type": "clap",
                        "timestamp_seconds": timestamp,
                        "duration_seconds": 0.1,
                        "confidence": 0.7,
                    })

        except Exception:
            pass
        return events

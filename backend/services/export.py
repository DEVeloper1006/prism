"""Export services for FCPXML, EDL, and CSV."""

import logging
from xml.etree.ElementTree import Element, SubElement, tostring

logger = logging.getLogger("[EXPORT]")


class ExportService:
    def to_fcpxml(self, clips: list[dict]) -> str:
        root = Element("fcpxml", version="1.11")
        resources = SubElement(root, "resources")
        library = SubElement(root, "library")
        event = SubElement(library, "event", name="PRISM Export")
        project = SubElement(event, "project", name="PRISM Assembly")
        sequence = SubElement(project, "sequence", format="r1")
        spine = SubElement(sequence, "spine")

        offset = 0
        for i, clip in enumerate(clips):
            duration = clip.get("duration_seconds") or 10.0
            fps = clip.get("fps") or 24.0
            dur_frames = int(duration * fps)

            fmt_id = f"r{i + 2}"
            fmt = SubElement(resources, "format",
                             id=fmt_id,
                             name=clip.get("resolution") or "1920x1080")
            fmt.set("frameDuration", f"1/{int(fps)}s")
            fmt.set("width", str(int((clip.get("resolution") or "1920x1080").split("x")[0])))
            fmt.set("height", str(int((clip.get("resolution") or "1920x1080").split("x")[-1])))

            asset_id = f"a{i + 1}"
            asset = SubElement(resources, "asset",
                               id=asset_id,
                               name=clip.get("id", f"clip_{i}"),
                               src=f"file://{clip.get('file_path', '')}",
                               format=fmt_id)
            asset.set("duration", f"{dur_frames}/{int(fps)}s")

            clip_el = SubElement(spine, "asset-clip",
                                 ref=asset_id,
                                 name=clip.get("id", f"clip_{i}"),
                                 offset=f"{int(offset * fps)}/{int(fps)}s",
                                 duration=f"{dur_frames}/{int(fps)}s")

            markers = clip.get("_markers", [])
            for marker in markers:
                SubElement(clip_el, "marker",
                           start=f"{int(marker['timestamp_seconds'] * fps)}/{int(fps)}s",
                           value=marker.get("note", ""))

            offset += duration

        return '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n' + tostring(root, encoding="unicode")

    def to_edl(self, clips: list[dict]) -> str:
        lines = ["TITLE: PRISM Export", "FCM: NON-DROP FRAME", ""]

        for i, clip in enumerate(clips, 1):
            duration = clip.get("duration_seconds") or 10.0
            fps = clip.get("fps") or 24.0

            src_in = self._tc(0, fps)
            src_out = self._tc(duration, fps)
            rec_in = self._tc(sum(
                (c.get("duration_seconds") or 0) for c in clips[:i - 1]
            ), fps)
            rec_out = self._tc(
                sum((c.get("duration_seconds") or 0) for c in clips[:i]), fps
            )

            lines.append(
                f"{i:03d}  {clip.get('id', 'AX')[:8]:8s} V     C        "
                f"{src_in} {src_out} {rec_in} {rec_out}"
            )
            if clip.get("scene_caption"):
                lines.append(f"* {clip['scene_caption']}")
            lines.append("")

        return "\n".join(lines)

    def to_csv(self, clips: list[dict]) -> str:
        if not clips:
            return ""
        headers = list(clips[0].keys())
        lines = [",".join(headers)]
        for clip in clips:
            row = [str(clip.get(h, "")).replace(",", ";") for h in headers]
            lines.append(",".join(row))
        return "\n".join(lines)

    def _tc(self, seconds: float, fps: float) -> str:
        total_frames = int(seconds * fps)
        f = total_frames % int(fps)
        s = (total_frames // int(fps)) % 60
        m = (total_frames // (int(fps) * 60)) % 60
        h = total_frames // (int(fps) * 3600)
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

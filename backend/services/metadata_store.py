"""SQLite metadata store for structured clip data."""

import json
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger("[STORE:METADATA]")

SCHEMA_PATH = Path(__file__).parent.parent / "db" / "schema.sql"


class MetadataStore:
    def __init__(self, db_path: Path, encryption_key: str | None = None) -> None:
        self.db_path = db_path
        self.encryption_key = encryption_key
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

        schema = SCHEMA_PATH.read_text()
        self._conn.executescript(schema)
        self._conn.commit()
        logger.info("Database initialized at %s", self.db_path)

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not initialized")
        return self._conn

    def insert_clip(self, clip_data: dict) -> None:
        cols = [
            "id", "file_path", "file_hash", "duration_seconds", "resolution",
            "fps", "codec", "color_space", "audio_channels", "camera", "lens",
            "focal_length", "iso", "gps_lat", "gps_lon", "file_size_bytes",
            "created_at", "scene_caption", "shot_type", "has_dialogue",
            "sharpness_score", "exposure_score", "stability_score", "color_score",
            "audio_quality", "dominant_colors", "lut_applied",
            "duplicate_group_id", "is_best_in_group",
        ]
        present = [c for c in cols if c in clip_data]
        placeholders = ", ".join("?" for _ in present)
        col_names = ", ".join(present)
        values = [clip_data[c] for c in present]

        self.conn.execute(
            f"INSERT OR REPLACE INTO clips ({col_names}) VALUES ({placeholders})",
            values,
        )
        self.conn.commit()

    def get_clip(self, clip_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM clips WHERE id = ?", (clip_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_clips(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None
    ) -> list[dict]:
        query = "SELECT * FROM clips"
        params: list = []
        conditions = self._build_conditions(filters, params)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY ingested_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def count_clips(self, filters: dict | None = None) -> int:
        query = "SELECT COUNT(*) FROM clips"
        params: list = []
        conditions = self._build_conditions(filters, params)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        row = self.conn.execute(query, params).fetchone()
        return row[0] if row else 0

    def filter_by_ids(
        self, clip_ids: list[str], filters: dict | None = None
    ) -> list[dict]:
        if not clip_ids:
            return []
        placeholders = ", ".join("?" for _ in clip_ids)
        query = f"SELECT * FROM clips WHERE id IN ({placeholders})"
        params: list = list(clip_ids)
        conditions = self._build_conditions(filters, params)
        if conditions:
            query += " AND " + " AND ".join(conditions)
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def delete_clip(self, clip_id: str) -> None:
        self.conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
        self.conn.commit()

    def _build_conditions(
        self, filters: dict | None, params: list
    ) -> list[str]:
        if not filters:
            return []
        conditions: list[str] = []
        if filters.get("resolution"):
            conditions.append("resolution = ?")
            params.append(filters["resolution"])
        if filters.get("camera"):
            conditions.append("camera = ?")
            params.append(filters["camera"])
        if filters.get("fps"):
            conditions.append("fps = ?")
            params.append(filters["fps"])
        if filters.get("quality_min") is not None:
            conditions.append("sharpness_score >= ?")
            params.append(filters["quality_min"])
        if filters.get("has_dialogue") is not None:
            conditions.append("has_dialogue = ?")
            params.append(filters["has_dialogue"])
        if filters.get("shot_type"):
            conditions.append("shot_type = ?")
            params.append(filters["shot_type"])
        if filters.get("date_from"):
            conditions.append("created_at >= ?")
            params.append(filters["date_from"])
        if filters.get("date_to"):
            conditions.append("created_at <= ?")
            params.append(filters["date_to"])
        return conditions

    # --- Face clusters ---

    def insert_face_cluster(self, label: str | None, encoding: bytes | None, rep_path: str | None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO face_clusters (label, encoding, representative_face_path) VALUES (?, ?, ?)",
            (label, encoding, rep_path),
        )
        self.conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def list_face_clusters(self) -> list[dict]:
        rows = self.conn.execute(
            """SELECT fc.id, fc.label, fc.representative_face_path, fc.created_at,
                      COUNT(fa.id) as count
               FROM face_clusters fc
               LEFT JOIN face_appearances fa ON fa.cluster_id = fc.id
               GROUP BY fc.id
               ORDER BY count DESC"""
        ).fetchall()
        return [dict(r) for r in rows]

    def insert_face_appearance(self, data: dict) -> None:
        self.conn.execute(
            """INSERT INTO face_appearances
               (cluster_id, clip_id, timestamp_seconds, bbox_x, bbox_y, bbox_w, bbox_h, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["cluster_id"], data["clip_id"], data["timestamp_seconds"],
             data["bbox_x"], data["bbox_y"], data["bbox_w"], data["bbox_h"],
             data.get("confidence")),
        )
        self.conn.commit()

    def get_clips_for_face(self, cluster_id: int) -> list[dict]:
        rows = self.conn.execute(
            """SELECT DISTINCT c.* FROM clips c
               JOIN face_appearances fa ON fa.clip_id = c.id
               WHERE fa.cluster_id = ?
               ORDER BY c.ingested_at DESC""",
            (cluster_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Transcripts ---

    def insert_transcript_segment(self, data: dict) -> None:
        self.conn.execute(
            """INSERT INTO transcripts (clip_id, speaker_label, start_time, end_time, text, confidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data["clip_id"], data.get("speaker_label"), data["start_time"],
             data["end_time"], data["text"], data.get("confidence")),
        )
        self.conn.commit()

    def get_transcript(self, clip_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM transcripts WHERE clip_id = ? ORDER BY start_time",
            (clip_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Audio events ---

    def insert_audio_event(self, data: dict) -> None:
        self.conn.execute(
            """INSERT INTO audio_events (clip_id, event_type, timestamp_seconds, duration_seconds, confidence)
               VALUES (?, ?, ?, ?, ?)""",
            (data["clip_id"], data["event_type"], data["timestamp_seconds"],
             data.get("duration_seconds"), data.get("confidence")),
        )
        self.conn.commit()

    def get_audio_events(self, clip_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM audio_events WHERE clip_id = ? ORDER BY timestamp_seconds",
            (clip_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Markers ---

    def insert_marker(self, data: dict) -> int:
        cursor = self.conn.execute(
            "INSERT INTO markers (clip_id, timestamp_seconds, note, color) VALUES (?, ?, ?, ?)",
            (data["clip_id"], data["timestamp_seconds"], data.get("note"), data.get("color", "blue")),
        )
        self.conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get_markers(self, clip_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM markers WHERE clip_id = ? ORDER BY timestamp_seconds",
            (clip_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Smart collections ---

    def insert_collection(self, name: str, rules: str) -> int:
        cursor = self.conn.execute(
            "INSERT INTO smart_collections (name, rules) VALUES (?, ?)",
            (name, rules),
        )
        self.conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def list_collections(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM smart_collections ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_collection(self, collection_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM smart_collections WHERE id = ?", (collection_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_collection_clips(self, collection_id: int) -> list[dict]:
        coll = self.get_collection(collection_id)
        if not coll:
            return []
        rules = json.loads(coll["rules"])
        return self.list_clips(filters=rules)

    # --- Storyboards ---

    def insert_storyboard(self, name: str, mode: str, cells: str) -> int:
        cursor = self.conn.execute(
            "INSERT INTO storyboards (name, mode, cells) VALUES (?, ?, ?)",
            (name, mode, cells),
        )
        self.conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get_storyboard(self, storyboard_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM storyboards WHERE id = ?", (storyboard_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_storyboards(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM storyboards ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def update_storyboard(self, storyboard_id: int, name: str | None = None, cells: str | None = None) -> None:
        updates: list[str] = []
        params: list = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if cells is not None:
            updates.append("cells = ?")
            params.append(cells)
        if not updates:
            return
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(storyboard_id)
        self.conn.execute(
            f"UPDATE storyboards SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self.conn.commit()

    # --- Watch config ---

    def get_watch_config(self) -> dict | None:
        row = self.conn.execute("SELECT * FROM watch_config WHERE id = 1").fetchone()
        return dict(row) if row else None

    def set_watch_config(self, folder_path: str | None, active: bool) -> None:
        self.conn.execute(
            """INSERT INTO watch_config (id, folder_path, active) VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET folder_path = ?, active = ?, last_scan = CURRENT_TIMESTAMP""",
            (folder_path, active, folder_path, active),
        )
        self.conn.commit()

    # --- Duplicates ---

    def get_duplicate_groups(self) -> list[dict]:
        rows = self.conn.execute(
            """SELECT duplicate_group_id, GROUP_CONCAT(id) as clip_ids
               FROM clips WHERE duplicate_group_id IS NOT NULL
               GROUP BY duplicate_group_id"""
        ).fetchall()
        groups = []
        for row in rows:
            clip_ids = row["clip_ids"].split(",")
            clips = self.filter_by_ids(clip_ids)
            best = next((c for c in clips if c.get("is_best_in_group")), clips[0] if clips else None)
            groups.append({
                "group_id": row["duplicate_group_id"],
                "clips": clips,
                "best_clip_id": best["id"] if best else None,
            })
        return groups

    # --- Audit log ---

    def log_action(self, action: str, details: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO audit_log (action, details) VALUES (?, ?)",
            (action, details),
        )
        self.conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

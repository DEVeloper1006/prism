CREATE TABLE IF NOT EXISTS clips (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    duration_seconds REAL,
    resolution TEXT,
    fps REAL,
    codec TEXT,
    color_space TEXT,
    audio_channels INTEGER,
    camera TEXT,
    lens TEXT,
    focal_length TEXT,
    iso INTEGER,
    gps_lat REAL,
    gps_lon REAL,
    file_size_bytes INTEGER,
    created_at TEXT,
    scene_caption TEXT,
    has_dialogue BOOLEAN DEFAULT FALSE,
    sharpness_score INTEGER,
    exposure_score INTEGER,
    stability_score INTEGER,
    color_score INTEGER,
    audio_quality TEXT,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_hash)
);

CREATE TABLE IF NOT EXISTS face_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT,
    representative_face_path TEXT,
    encoding BLOB,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS face_appearances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER REFERENCES face_clusters(id),
    clip_id TEXT REFERENCES clips(id),
    timestamp_seconds REAL,
    bbox_x INTEGER,
    bbox_y INTEGER,
    bbox_w INTEGER,
    bbox_h INTEGER,
    confidence REAL
);

CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id TEXT REFERENCES clips(id),
    speaker_label TEXT,
    start_time REAL,
    end_time REAL,
    text TEXT,
    confidence REAL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clips_hash ON clips(file_hash);
CREATE INDEX IF NOT EXISTS idx_clips_camera ON clips(camera);
CREATE INDEX IF NOT EXISTS idx_clips_resolution ON clips(resolution);
CREATE INDEX IF NOT EXISTS idx_clips_sharpness ON clips(sharpness_score);
CREATE INDEX IF NOT EXISTS idx_face_appearances_cluster ON face_appearances(cluster_id);
CREATE INDEX IF NOT EXISTS idx_face_appearances_clip ON face_appearances(clip_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_clip ON transcripts(clip_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_text ON transcripts(text);

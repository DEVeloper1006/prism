# PRISM — Claude Code Project Context

## What Is This Project?

PRISM (Post-production Review & Intelligent Scene Manager) is a desktop application that automates the most time-consuming phase of filmmaking: footage review and organization. After a shoot, filmmakers return with hours of raw footage across dozens of camera cards. Before editing can begin, every clip must be watched, logged, tagged, and organized. On a real production, this takes 2-5 days. PRISM reduces it to minutes.

You point PRISM at a folder of raw footage. It processes every clip through five parallel AI analysis tracks (visual intelligence, audio transcription, technical quality scoring, face clustering, and metadata extraction). It builds a searchable index. You find any shot with natural language in seconds. Then it suggests clips for your shot list and exports directly into your NLE (DaVinci Resolve, Final Cut Pro, Premiere Pro).

**This is a Tauri desktop app — not a web app.** Filmmakers' media libraries are local (SSDs, NAS drives, external drives). Uploading to a server is a non-starter. All AI models run locally. No footage ever leaves the machine. This is both a performance decision and a security requirement — filmmakers routinely work under NDA.

## Why Existing Tools Fail

DaVinci Resolve and Premiere Pro have media pools but zero intelligence — they show thumbnails and metadata, and you do the rest manually. Lightroom has smart search but only handles photos. Frame.io handles review workflows but not AI analysis. No tool connects visual understanding, speech transcription, face recognition, and quality scoring into a single searchable pipeline. PRISM fills that gap.

## System Design Principles

These five principles govern every architectural decision in the project. If you're unsure how to implement something, refer back to these.

### 1. Offline-First, Privacy-First
All AI models run locally via Ollama and direct Python libraries. No API calls to OpenAI, Anthropic, or any cloud service. No telemetry. No network requests after install. Footage metadata stays on the machine. This is non-negotiable — filmmakers work under NDA, and studios will not adopt tools that transmit any data externally.

### 2. Process Once, Query Forever
Ingestion is computationally expensive (VLM inference, CLIP encoding, Whisper transcription, face detection). But it happens once per clip. After ingestion, every search, filter, and similarity lookup is a fast vector/SQL query. The system amortizes heavy upfront compute over unlimited future queries. Design every storage layer for read speed, not write speed.

### 3. Parallelism by Default
The five analysis tracks are independent — they don't share state during processing. They run concurrently via a worker pool (ProcessPoolExecutor for CPU-bound AI inference, ThreadPoolExecutor for I/O-bound metadata extraction). Total ingestion time equals the slowest track, not the sum of all tracks. A progress event bus pushes per-track updates to the UI via WebSocket.

### 4. Separation of Storage Concerns
Don't put everything in one database. Each storage layer is optimized for its access pattern:
- **ChromaDB** → vector embeddings (optimized for similarity search via HNSW index)
- **SQLite** → structured metadata (optimized for filtering, joining, sorting via B-tree indexes)
- **Filesystem** → thumbnails, keyframes, face crops, transcript JSON (optimized for sequential I/O)

This separation means you can upgrade, replace, or scale any layer independently.

### 5. Non-Destructive Sidecar Architecture
PRISM never modifies original footage. All analysis data lives in a `.prism/` sidecar directory alongside the media folder. Delete `.prism/` and your files are untouched. Move footage to a new drive, re-link in PRISM, and it detects existing `.prism/` data without re-processing. Same philosophy as `.git/` folders and Lightroom catalogs — portable, non-destructive, self-contained.

## Architecture — Three-Layer Desktop App

```
┌──────────────────────────────────────────────────────┐
│  TAURI SHELL (Rust)                                   │
│  Native OS integration: file dialogs, window mgmt,    │
│  filesystem permissions, OS keychain, Python sidecar   │
│  spawn, session token generation                       │
└──────────┬──────────────────────────────┬─────────────┘
           │ IPC (invoke commands)         │ spawn + token
           │                               │
┌──────────▼─────────────┐    ┌───────────▼─────────────┐
│  REACT FRONTEND (TS)    │    │  PYTHON BACKEND (FastAPI)│
│  Vite + Tailwind        │    │  Port 8420 on 127.0.0.1  │
│  4 views:               │◄──►│  AI pipeline, search,     │
│  • Clip Browser         │HTTP│  storage, export           │
│  • Timeline             │ +  │                            │
│  • Transcript           │ WS │  5 ingestion tracks        │
│  • Assembly             │    │  Hybrid search engine       │
└─────────────────────────┘    └────────────────────────────┘
                                         │
                    ┌────────────────────┬┴──────────────────┐
                    │                    │                    │
              ┌─────▼─────┐      ┌──────▼──────┐    ┌───────▼──────┐
              │  ChromaDB  │      │   SQLite    │    │  Filesystem  │
              │  (vectors) │      │  (metadata) │    │  (.prism/)   │
              └────────────┘      └─────────────┘    └──────────────┘
```

### How the Layers Communicate

**Tauri ↔ React:** Tauri's IPC system. React calls `invoke("command_name")` to execute Rust functions. Used for native OS features only — file picker dialogs, reading OS keychain, getting system info. Not used for data-heavy operations.

**React ↔ Python:** Standard HTTP (REST) for request/response operations (search, get clip details, start ingestion). WebSocket for real-time streaming (ingestion progress updates, live pipeline status). React treats the Python backend like any API — `fetch("http://127.0.0.1:8420/...")`.

**Tauri → Python:** On app startup, Tauri spawns the Python process as a sidecar, passing a randomly generated session token as a CLI argument. Python's FastAPI middleware validates this token on every request.

## The .prism/ Sidecar Directory

When the user points PRISM at a folder, it creates this structure alongside their footage:

```
Media_Folder/
├── A001_C001.mp4                  ← ORIGINAL (never touched)
├── A001_C002.mp4
├── ...
└── .prism/                        ← PRISM'S DATA (all generated)
    ├── index.db                   ← SQLite: all structured metadata
    ├── index.db.key               ← NOT stored here — key is in OS keychain
    ├── chroma/                    ← ChromaDB: vector embeddings
    │   ├── chroma.sqlite3
    │   └── ...
    ├── thumbs/                    ← Generated thumbnails (WebP, 320px wide)
    │   ├── A001_C001_thumb.webp
    │   └── ...
    ├── keyframes/                 ← Scene-change keyframes (JPEG)
    │   ├── A001_C001_kf_001.jpg
    │   └── ...
    ├── transcripts/               ← Whisper output (JSON with word timestamps)
    │   ├── A001_C002.json
    │   └── ...
    ├── faces/                     ← Face crop cache for clustering UI
    │   ├── cluster_0/
    │   ├── cluster_1/
    │   └── ...
    └── manifest.json              ← Tracks which files have been processed + checksums
```

The `manifest.json` enables incremental ingestion — on re-scan, PRISM checksums every file and only processes new or modified clips. Existing analysis data is preserved.

## Ingestion Pipeline — 5 Parallel Tracks

All tracks run concurrently via a job orchestrator. Each track is independent — no shared state during processing. The orchestrator manages the worker pool and pushes per-track progress events via WebSocket.

### Track 1: Visual Intelligence
- **Input:** Video file
- **Process:** PySceneDetect detects scene boundaries → extract keyframes at each boundary. Each keyframe → OpenCLIP ViT-L/14 → 768-dimensional embedding vector. VLM (Moondream2 via Ollama) generates natural language scene description per segment.
- **Output:** CLIP embeddings (stored in ChromaDB), scene captions (stored in SQLite), keyframe images (stored in `.prism/keyframes/`)
- **Why:** Powers natural language search. "Sunset wide shot with warm tones" → CLIP encodes query → cosine similarity against all clip embeddings → ranked results.

### Track 2: Audio Intelligence
- **Input:** Audio track extracted via ffmpeg
- **Process:** Whisper.cpp (C++ port — 3-5x faster than Python Whisper, runs on CPU or GPU) → word-level transcription with timestamps. pyannote.audio → speaker diarization (clusters who is speaking when). RMS + peak analysis → audio quality flags (clipping, low signal, background noise).
- **Output:** Timestamped transcript with speaker labels (stored as JSON in `.prism/transcripts/`), audio quality scores (stored in SQLite)
- **Why:** Editors search for specific dialogue constantly. Click a word → jump to that exact frame. Speaker diarization answers "show me everything Person A said."

### Track 3: Technical Quality Scoring
- **Input:** Video frames (sampled at 1fps)
- **Process:** Laplacian variance → sharpness score. Histogram spread analysis → exposure score. Optical flow magnitude between consecutive frames → stability score (high variance = handheld/shaky). Color histogram consistency → color drift detection.
- **Output:** Per-clip quality scores 0-100 for sharpness, exposure, stability, color consistency (stored in SQLite)
- **Why:** Automated "selects" pass. Filter to quality > 70 and you've cut review time in half. Flags unusable footage before a human wastes time watching it.

### Track 4: Face Intelligence
- **Input:** Keyframes from Track 1
- **Process:** face_recognition library (dlib-based) detects faces in keyframes → extracts 128-dim face encodings. DBSCAN clustering groups encodings by visual similarity — no training data, no labels needed. Each cluster = one person across all footage.
- **Output:** Face clusters with clip timestamps and bounding boxes (stored in SQLite + face crop images in `.prism/faces/`)
- **Why:** "Show me every shot of the interviewee" across 200 clips, instantly, without manual tagging. Click a face cluster → see every clip that person appears in.

### Track 5: Metadata Extraction
- **Input:** Video file + filesystem
- **Process:** ffprobe → codec, resolution, fps, duration, audio channels, color space, bitrate. Pillow/ExifTool → camera model, lens, focal length, ISO, GPS coordinates (if embedded in container). Filesystem → file size, creation date, folder path.
- **Output:** Structured metadata rows (stored in SQLite)
- **Why:** Foundation layer. Every filter query ("show me all 4K clips from Camera A at 24fps") depends on this being extracted and indexed. Fastest track — runs in seconds.

### Pipeline Orchestrator Design
```
User clicks "Ingest Folder"
        │
        ▼
┌─ File Scanner ──────────────────────────────────────┐
│  Walk directory → checksum each file → compare to   │
│  manifest.json → build list of new/modified files    │
└──────────────────────┬──────────────────────────────┘
                       │ job list
                       ▼
┌─ Worker Pool ───────────────────────────────────────┐
│  ProcessPoolExecutor(max_workers=cpu_count - 1)     │
│                                                      │
│  For each file, spawn 5 track tasks:                │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  │ T1   │ │ T2   │ │ T3   │ │ T4   │ │ T5   │     │
│  │Visual│ │Audio │ │Tech  │ │Face  │ │Meta  │     │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘     │
│     │        │        │        │        │           │
│     ▼        ▼        ▼        ▼        ▼           │
│  ┌─ Storage Writes ──────────────────────┐          │
│  │ ChromaDB ← vectors                    │          │
│  │ SQLite   ← metadata, scores, faces    │          │
│  │ FS       ← thumbs, keyframes, crops   │          │
│  └────────────────────────────────────────┘          │
└──────────────────────┬──────────────────────────────┘
                       │ progress events (per track, per file)
                       ▼
              WebSocket → React UI
              (live progress bars, clips appear as they finish)
```

## Hybrid Search Architecture

Two fundamentally different query types require two different engines:

### Semantic Search (ChromaDB)
Natural language queries about visual content:
- "sunset over water with warm tones"
- "interview with bookshelf background"
- "close-up of hands working"

The query text is encoded by the same CLIP model used during ingestion → cosine similarity against all clip embeddings → ranked by visual similarity score. Understands meaning, not keywords.

### Filtered Search (SQLite)
Exact metadata constraints:
- `resolution = '4K' AND fps = 24`
- `camera = 'Sony A6700' AND has_dialogue = true`
- `sharpness > 80 AND date = '2026-07-01'`

Standard SQL WHERE clauses on indexed columns. Exact, fast, deterministic.

### Combined (Hybrid)
The real power is combining both: "sunset wide shot" WHERE resolution = 4K AND camera = "Sony A6700"

Implementation: ChromaDB returns top-100 clip IDs by semantic similarity → SQLite filters those IDs by metadata constraints → final ranked result set. This is the same pattern used by production search engines (Elasticsearch + vector plugins).

Endpoint: `POST /search`
```json
{
  "query": "sunset wide shot",        // semantic (optional)
  "filters": {                         // metadata (optional)
    "resolution": "3840x2160",
    "camera": "Sony A6700",
    "quality_min": 70
  },
  "top_k": 20
}
```

## Scalability Design — Handling 10,000+ Clips

### Lazy Thumbnail Loading
The clip grid uses Intersection Observer to load only visible thumbnails. Scroll down → new thumbnails load. Memory stays flat regardless of library size. Never load all thumbnails into memory at once.

### Incremental Ingestion
Adding new footage doesn't re-process the whole library. The file scanner checksums every file against `manifest.json`. Only new or modified files enter the pipeline. Moving or renaming files (same checksum) triggers a re-link, not a re-process.

### HNSW Vector Index
ChromaDB uses HNSW (Hierarchical Navigable Small World) indexing internally. This gives O(log n) approximate nearest neighbor search instead of brute-force O(n). 10,000 clips ≈ 10,000 vectors → <50ms query time.

### Pagination + Virtual Scrolling
The clip grid and transcript views use virtual scrolling — only DOM nodes for visible items exist in the browser. SQLite queries use LIMIT/OFFSET. The UI renders 50 items per page, not 10,000.

### Background Processing Queue
Ingestion runs as a background job queue. The UI remains fully responsive. Users can browse and search already-indexed clips while new ones are still processing. Progress is reported per-file and per-track.

### WAL Mode for SQLite
SQLite runs in WAL (Write-Ahead Logging) mode, which allows concurrent reads during writes. The ingestion pipeline can write new metadata while the search engine reads existing data without blocking.

## Security Architecture

### Layer 1: Session Token Authentication
Tauri generates a cryptographically random token on each app launch. This token is passed to the Python backend as a CLI argument and to the React frontend via Tauri IPC. Every HTTP request from React to Python includes `Authorization: Bearer <token>`. The FastAPI middleware rejects any request without a valid token. This prevents rogue processes on the same machine from accessing the API.

### Layer 2: Filesystem Sandboxing
The ingestion endpoint accepts a folder path as input — a path traversal attack vector. The backend must:
- Resolve the path to its canonical absolute form (resolve symlinks)
- Confirm it's within an allowed directory (the user-selected media root)
- Reject paths containing `../`, symlinks pointing outside the root, and system directories
- Tauri's capability system declares exactly which filesystem scopes the app can access in `capabilities/default.json`

### Layer 3: Encryption at Rest (SQLCipher)
The `.prism/index.db` SQLite database contains AI-generated descriptions of footage that may be under NDA. Use SQLCipher (drop-in encrypted replacement for SQLite, AES-256) to encrypt the database file. The encryption key derives from a passphrase set on first launch, stored in the OS keychain (macOS Keychain / Windows Credential Manager) via Tauri's secure storage plugin.

### Layer 4: Input Sanitization
- All SQLite queries use parameterized statements — never string interpolation
- Search query input is length-limited (500 chars) and character-set validated
- File paths are validated before any filesystem operation
- WebSocket messages are schema-validated before processing

### Layer 5: Multi-User / Team Mode (Future)
When scaling to studio teams sharing a NAS:
- File-level locking via SQLite WAL mode (single machine) or PostgreSQL migration (cross-network)
- Role-based access: lead editor (full access) vs junior editor (browse + search only)
- JWT session tokens with short expiry, signed with per-project secret
- Audit logging: who searched what, who exported what, who modified the index

### Layer 6: Dependency Security
- Pin all Python dependencies with exact versions + hashes in `requirements.txt`
- Run `pip audit` and `cargo audit` as part of the build process
- Minimize dependency surface — prefer stdlib where possible
- Rust backend is memory-safe by default (no buffer overflows)

### Security Flow Diagram
```
App Launch
    │
    ├─ Tauri generates random session token (32 bytes, hex)
    ├─ Tauri reads encryption key from OS keychain (or prompts for passphrase)
    ├─ Tauri spawns Python: `python main.py --token <token> --db-key <key>`
    ├─ Tauri sends token to React via IPC
    │
    ▼
Every API Request (React → Python)
    │
    ├─ React includes: Authorization: Bearer <token>
    ├─ FastAPI middleware: validate token → 401 if invalid
    ├─ Route handler: validate input schema (Pydantic)
    ├─ Service layer: parameterized queries, path validation
    ├─ SQLCipher: encrypted read/write
    └─ Audit logger: record action + timestamp
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest` | Start ingestion for a folder path |
| GET | `/ingest/status` | Current pipeline progress (per file, per track) |
| POST | `/ingest/cancel` | Cancel running ingestion |
| POST | `/search` | Hybrid search (semantic + filtered) |
| GET | `/clips` | Paginated clip list with filters |
| GET | `/clips/{id}` | Full clip detail (metadata + scores + caption + transcript) |
| GET | `/clips/{id}/thumbnail` | Serve thumbnail image |
| GET | `/clips/{id}/keyframes` | List keyframe images for a clip |
| GET | `/faces` | List all face clusters with counts |
| GET | `/faces/{cluster_id}/clips` | Clips containing a specific face cluster |
| GET | `/transcript/{clip_id}` | Full transcript with word timestamps |
| POST | `/export/fcpxml` | Generate FCPXML from shot list |
| POST | `/export/edl` | Generate EDL from shot list |
| POST | `/export/csv` | Export metadata as CSV |
| GET | `/ws/progress` | WebSocket: ingestion progress stream |
| GET | `/health` | Backend health check |

## Repo Structure

```
prism/
├── CLAUDE.md                              # This file
├── AGENTS.md                              # Sub-agent definitions
├── README.md                              # Public docs
├── package.json                           # React + Vite dependencies
├── vite.config.ts                         # Vite config with Tauri plugin
├── tsconfig.json                          # Strict TypeScript
├── tailwind.config.ts                     # Custom colors, JetBrains Mono
├── index.html                             # Vite entry
│
├── src-tauri/                             # RUST LAYER
│   ├── Cargo.toml                         # Rust dependencies (tauri, serde, rand)
│   ├── tauri.conf.json                    # App config: name, window (1440x900), identifier
│   ├── capabilities/
│   │   └── default.json                   # Permissions: fs scope, shell, dialog, keychain
│   ├── src/
│   │   ├── main.rs                        # Entry: spawn Python sidecar, generate token
│   │   └── lib.rs                         # Commands: open_folder, get_token, keychain ops
│   └── icons/                             # App icons for all platforms
│
├── src/                                   # REACT LAYER
│   ├── main.tsx                           # React entry
│   ├── App.tsx                            # Root: view router + layout shell
│   ├── styles.css                         # Tailwind directives + custom scrollbar + glow
│   ├── components/
│   │   ├── TopBar.tsx                     # Project name, clip count, ingest status indicator
│   │   ├── ViewSwitcher.tsx               # Browser | Timeline | Transcript | Assembly tabs
│   │   ├── ClipBrowser.tsx                # Masonry grid with virtual scroll
│   │   ├── ClipCard.tsx                   # Thumbnail + duration + quality dot + badges
│   │   ├── ClipDetail.tsx                 # Right sidebar: AI analysis, scores, metadata
│   │   ├── SearchBar.tsx                  # Semantic + filter input with AI badge
│   │   ├── FilterPanel.tsx                # Resolution, fps, camera, quality, date range
│   │   ├── FaceSidebar.tsx                # Left sidebar: face clusters + shot type filters
│   │   ├── TimelineView.tsx               # Chronological track view of all footage
│   │   ├── TranscriptView.tsx             # Searchable dialogue with click-to-jump
│   │   ├── AssemblyWorkspace.tsx          # Shot list + AI suggestions + drag reorder
│   │   ├── ProgressOverlay.tsx            # Ingestion progress: per-file, per-track bars
│   │   ├── ScoreBar.tsx                   # Horizontal quality score bar (green/yellow/red)
│   │   └── LatencyChart.tsx               # Recharts sparkline for pipeline timing
│   ├── hooks/
│   │   ├── useWebSocket.ts               # WS connection with auto-reconnect
│   │   ├── useClipLibrary.ts             # Clip state: paginated fetch, search, filter
│   │   ├── useIngestionProgress.ts       # Real-time pipeline progress via WS
│   │   └── useVirtualScroll.ts           # Intersection observer for lazy loading
│   ├── lib/
│   │   ├── api.ts                         # Typed fetch wrappers for all Python endpoints
│   │   ├── tauri.ts                       # Typed invoke wrappers for Rust commands
│   │   ├── types.ts                       # All TypeScript interfaces
│   │   └── constants.ts                   # API URL, WS URL, color thresholds
│   └── assets/
│       └── prism-logo.svg
│
├── backend/                               # PYTHON LAYER
│   ├── main.py                            # FastAPI app: mount routers, auth middleware, CORS
│   ├── config.py                          # Settings via pydantic-settings (port, paths, token)
│   ├── requirements.txt                   # Pinned with exact versions
│   ├── auth.py                            # Token validation middleware
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py                # Job queue, worker pool, progress event bus
│   │   ├── scanner.py                     # File walker, checksum, manifest diffing
│   │   ├── visual.py                      # Track 1: PySceneDetect + OpenCLIP + VLM
│   │   ├── audio.py                       # Track 2: Whisper.cpp + pyannote + RMS
│   │   ├── technical.py                   # Track 3: Laplacian + histogram + optical flow
│   │   ├── faces.py                       # Track 4: face_recognition + DBSCAN
│   │   └── metadata.py                    # Track 5: ffprobe + ExifTool + filesystem
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vector_store.py                # ChromaDB: add, search, delete, get_count
│   │   ├── metadata_store.py              # SQLite/SQLCipher: CRUD, filtered queries
│   │   ├── search.py                      # Hybrid search: ChromaDB top-k → SQLite filter
│   │   ├── export.py                      # FCPXML, EDL, CSV generation
│   │   └── ws_manager.py                  # WebSocket broadcast for progress events
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                     # Pydantic: Clip, SearchQuery, IngestJob, FaceCluster
│   ├── db/
│   │   └── schema.sql                     # CREATE TABLE: clips, faces, clusters, transcripts, audit_log
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                    # Test fixtures: sample clips, mock pipeline
│       ├── test_search.py                 # Hybrid search: semantic, filtered, combined
│       ├── test_pipeline.py               # Track outputs, parallel execution, error handling
│       ├── test_auth.py                   # Token validation, missing token, invalid token
│       └── test_security.py               # Path traversal, SQL injection, input validation
│
└── scripts/
    ├── dev.sh                             # Start Python backend + Tauri dev mode
    ├── seed_demo.py                       # Generate sample clips with fake analysis data
    └── build.sh                           # Production build: Python bundled + Tauri build
```

## Database Schema (SQLite / SQLCipher)

```sql
CREATE TABLE clips (
    id TEXT PRIMARY KEY,                    -- filename-based unique ID
    file_path TEXT NOT NULL,                -- relative path from media root
    file_hash TEXT NOT NULL,                -- SHA-256 checksum
    duration_seconds REAL,
    resolution TEXT,                         -- "3840x2160"
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
    created_at TEXT,                         -- file creation timestamp
    scene_caption TEXT,                      -- VLM-generated description
    has_dialogue BOOLEAN DEFAULT FALSE,
    sharpness_score INTEGER,                -- 0-100
    exposure_score INTEGER,                 -- 0-100
    stability_score INTEGER,                -- 0-100
    color_score INTEGER,                    -- 0-100
    audio_quality TEXT,                     -- "clean", "noise", "clipping"
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_hash)
);

CREATE TABLE face_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT,                              -- user-assigned name (nullable)
    representative_face_path TEXT,           -- path to best face crop for UI
    encoding BLOB,                           -- average 128-dim encoding for the cluster
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE face_appearances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER REFERENCES face_clusters(id),
    clip_id TEXT REFERENCES clips(id),
    timestamp_seconds REAL,                  -- when in the clip the face appears
    bbox_x INTEGER,
    bbox_y INTEGER,
    bbox_w INTEGER,
    bbox_h INTEGER,
    confidence REAL
);

CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id TEXT REFERENCES clips(id),
    speaker_label TEXT,                      -- "Speaker_0", "Speaker_1" (from diarization)
    start_time REAL,                         -- seconds
    end_time REAL,
    text TEXT,
    confidence REAL
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,                    -- "search", "export", "ingest", "delete"
    details TEXT,                             -- JSON blob with action-specific data
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX idx_clips_hash ON clips(file_hash);
CREATE INDEX idx_clips_camera ON clips(camera);
CREATE INDEX idx_clips_resolution ON clips(resolution);
CREATE INDEX idx_clips_sharpness ON clips(sharpness_score);
CREATE INDEX idx_face_appearances_cluster ON face_appearances(cluster_id);
CREATE INDEX idx_face_appearances_clip ON face_appearances(clip_id);
CREATE INDEX idx_transcripts_clip ON transcripts(clip_id);
CREATE INDEX idx_transcripts_text ON transcripts(text);
```

## Coding Conventions

### Python (backend/)
- Python 3.11+
- Type hints on all function signatures
- Docstrings on all public classes and functions
- Pydantic for all data models and validation
- Async FastAPI endpoints with `uvicorn`
- Logging via Python `logging` module with structured format: `[PIPELINE:T1]`, `[SEARCH]`, `[AUTH]`
- Tests using `pytest` with `httpx.AsyncClient` for endpoint testing
- Security: parameterized SQL everywhere, path validation on every filesystem op

### TypeScript / React (src/)
- Strict TypeScript — no `any` types
- All API response types defined in `lib/types.ts`
- Functional components with hooks — no class components
- `"use client"` only where browser APIs are needed (rare — most components are client by default in Vite)
- Tailwind CSS for all styling — no CSS modules, no styled-components
- Virtual scrolling for any list that could exceed 100 items

### Rust (src-tauri/)
- Minimal Rust — only what Tauri requires (commands, setup, sidecar spawn)
- Use `serde` for serialization between Rust and JS
- Error handling with `Result` types — never `unwrap()` in production code

### Design Language
- Dark background: `#141416` (base), `#1C1C1F` (panels), `#232326` (surfaces)
- Accent: `#6C5CE7` (purple — PRISM's signature color)
- Semantic colors: `#2ED47A` (good/pass), `#FFB347` (warning), `#FF6B6B` (bad/fail), `#4ECDC4` (info)
- Monospace: JetBrains Mono (clip IDs, metadata, timestamps, scores)
- Sans: Inter (UI labels, descriptions, body text)
- Minimum window: 1200 x 800px
- Design reference: DaVinci Resolve media pool + Lightroom library hybrid

### Git
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `security:`
- Branch naming: `feat/visual-track`, `feat/hybrid-search`, `fix/path-traversal`
- Never commit: `.prism/`, `node_modules/`, `__pycache__/`, `.env`, `target/` (Rust build), model weights

## Current Status

- [ ] Project scaffold (Tauri + React + Python backend structure)
- [ ] Security: token auth middleware, path validation, SQLCipher integration
- [ ] Pipeline: orchestrator, scanner, worker pool
- [ ] Track 1: Visual Intelligence (PySceneDetect + OpenCLIP + VLM)
- [ ] Track 2: Audio Intelligence (Whisper.cpp + pyannote)
- [ ] Track 3: Technical Scoring (OpenCV quality metrics)
- [ ] Track 4: Face Intelligence (face_recognition + DBSCAN)
- [ ] Track 5: Metadata Extraction (ffprobe + ExifTool)
- [ ] Storage: ChromaDB + SQLCipher + filesystem sidecar
- [ ] Hybrid Search Engine
- [ ] UI: Clip Browser with virtual scroll
- [ ] UI: Timeline View
- [ ] UI: Transcript View with click-to-jump
- [ ] UI: Assembly Workspace with AI suggestions
- [ ] Export: FCPXML, EDL, CSV, contact sheet
- [ ] Testing: security, pipeline, search, auth
# PRISM — Agent Definitions

This file defines specialized sub-agents for Claude Code to delegate tasks across the three layers of the PRISM desktop application. Each agent has scoped responsibility, access to specific directories, and rules to follow.

---

## Agent: Shell

**Description:** Handles the Tauri/Rust layer — native OS integration, Python sidecar management, security token generation, and filesystem permissions.

**Scope:** `src-tauri/`

**Rules:**
- Minimal Rust — only write what Tauri requires. Don't build business logic in Rust; that belongs in the Python backend.
- On app startup (`main.rs` setup hook): generate a 32-byte random hex token, store it in app state, pass it to the Python sidecar as a `--token` CLI argument, and make it available to the React frontend via a Tauri command.
- The Python sidecar is spawned via `Command::new("python3").args(...)`. It must be killed on app close (handle the `close_requested` event).
- All Tauri commands use `Result<T, String>` return types — never `unwrap()` or `expect()` in production paths.
- `tauri.conf.json` settings: window title "PRISM", default size 1440x900, minimum size 1200x800, decorations true, `identifier` = `com.prism.app`.
- `capabilities/default.json` must declare filesystem scope limited to user-selected directories only. Use `dialog:allow-open` for folder picker. Do not allow unrestricted filesystem access.
- Use Tauri's secure storage plugin (`tauri-plugin-store` or OS keychain) for the SQLCipher encryption passphrase — never store secrets on the regular filesystem.
- Use `serde` for serialization in all IPC between Rust and JavaScript.

---

## Agent: Frontend

**Description:** Handles the React/TypeScript UI layer — all four views (Clip Browser, Timeline, Transcript, Assembly), components, hooks, and styling.

**Scope:** `src/`

**Rules:**
- Vite + React + TypeScript in strict mode — no `any` types anywhere.
- Tailwind CSS for all styling. Custom theme in `tailwind.config.ts`: colors (`bg-prism-base: #141416`, `bg-prism-panel: #1C1C1F`, `bg-prism-surface: #232326`, `accent: #6C5CE7`, `score-good: #2ED47A`, `score-warn: #FFB347`, `score-bad: #FF6B6B`, `info: #4ECDC4`), fonts (JetBrains Mono for data, Inter for UI).
- **App.tsx** is the root layout: TopBar at top, ViewSwitcher below it, then a three-column layout (FaceSidebar left, active view center, ClipDetail right). The right sidebar only renders when a clip is selected.
- **Clip Browser** uses virtual scrolling (Intersection Observer via `useVirtualScroll` hook). Only DOM nodes for visible clip cards exist. Pagination via `LIMIT/OFFSET` from the Python API. Never load all clips into memory.
- **SearchBar** sends to `POST /search`. It combines a text input (semantic query) with filter dropdowns (resolution, fps, camera, quality threshold, date range). Debounce input by 300ms before firing requests.
- **TranscriptView** renders word-level timestamps from Whisper output. Clicking any word calls the parent to seek the associated clip to that timecode. Highlight the currently active speaker in the accent color.
- **AssemblyWorkspace** is a drag-and-drop shot list. Each row shows a shot description + PRISM's suggested clip match (from semantic search) + confidence score. Users can accept, reject, or manually pick a different clip. Export buttons at the bottom (FCPXML, EDL, CSV).
- **ProgressOverlay** appears during ingestion as a modal overlay. Shows per-file progress (which files are queued, processing, done) and per-track progress (5 track bars per file). Data comes from the WebSocket at `/ws/progress`. The overlay is dismissable — ingestion continues in background.
- **API calls** (`lib/api.ts`): every `fetch` call includes `Authorization: Bearer <token>` header. The token is retrieved once on mount via `invoke("get_session_token")` from Tauri and stored in a React context.
- **Tauri calls** (`lib/tauri.ts`): typed wrappers for `invoke("open_folder_dialog")`, `invoke("get_session_token")`, `invoke("get_system_info")`. Import `invoke` from `@tauri-apps/api/core`.
- No loading spinners in the clip grid — data loads incrementally. Show a "Drop a folder to begin" empty state when no project is loaded.
- All images (thumbnails, keyframes, face crops) are served from the Python backend at `/clips/{id}/thumbnail` etc., not read directly from the filesystem via Tauri. This keeps all filesystem access in the Python layer where path validation happens.

---

## Agent: Backend

**Description:** Handles the Python/FastAPI layer — AI ingestion pipeline, search engine, storage, security middleware, export, and all API endpoints.

**Scope:** `backend/`

**Rules:**

### Security (applies to ALL endpoints)
- `auth.py` middleware: extract `Authorization: Bearer <token>` from every request. Compare against the token passed via `--token` CLI arg on startup. Return 401 if missing or invalid. No exceptions — even `/health` requires auth.
- Path validation: every endpoint that accepts a file path must resolve it to canonical absolute form, reject `../` traversal, reject symlinks pointing outside the media root, and reject system directories. Create a `validate_path(path, allowed_root)` utility in `auth.py`.
- All SQLite queries use parameterized statements (`?` placeholders) — never f-strings or string interpolation for SQL.
- Search query input: max 500 characters, strip control characters, validate UTF-8.
- Audit logging: every search, export, ingest, and delete action writes to the `audit_log` table with action type, details JSON, and timestamp.

### API Server
- FastAPI with async endpoints, served by `uvicorn` on `127.0.0.1:8420` (bind to loopback only, never `0.0.0.0`).
- CORS configured to allow only `tauri://localhost` and `http://localhost:1420` (Vite dev server).
- Startup event: initialize SQLCipher connection (key from `--db-key` CLI arg), initialize ChromaDB persistent client, verify Ollama is running.
- Shutdown event: close DB connections, cancel running pipeline jobs.
- All request/response models in `models/schemas.py` using Pydantic v2.

### Ingestion Pipeline
- `pipeline/orchestrator.py` is the central coordinator. It receives a folder path, runs the scanner, builds a job queue, manages the worker pool, and pushes progress events via the WebSocket manager.
- `pipeline/scanner.py` walks the directory, checksums files (SHA-256, first 1MB + last 1MB + filesize for speed), diffs against `manifest.json`, and returns a list of new/modified files.
- Worker pool: `ProcessPoolExecutor(max_workers=os.cpu_count() - 1)` for CPU-bound tracks (T1 visual, T3 technical, T4 faces). `ThreadPoolExecutor` for I/O-bound tracks (T2 audio via subprocess, T5 metadata via ffprobe subprocess).
- Each track function takes a file path + config and returns a structured result dict. Tracks must not share state. Tracks must handle errors gracefully — if one track fails on a clip, the other tracks' results are still saved, and the failure is logged.
- After all tracks complete for a clip, write results atomically: ChromaDB add, SQLite insert (single transaction), filesystem writes (thumbs, keyframes). Update `manifest.json`.
- Progress events: emit per-file and per-track via the WebSocket manager. Format: `{"type": "progress", "file": "A001_C001.mp4", "track": "visual", "status": "processing"|"done"|"error", "percent": 0-100}`.

### Search
- `services/search.py` implements hybrid search. If only semantic query → ChromaDB cosine search. If only filters → SQLite WHERE. If both → ChromaDB top-100 IDs → SQLite filter on those IDs → return intersection ranked by similarity.
- The semantic search endpoint must load the same CLIP model used during ingestion to encode the query text. Cache the model in memory — don't reload on every request.
- Search results return: clip_id, similarity_score (if semantic), thumbnail URL, scene_caption, quality scores, duration, resolution. Enough to render a ClipCard without a second API call.

### Storage
- ChromaDB: persistent mode, stored in `.prism/chroma/`. Collection name = project folder basename. Each document = one clip (or one keyframe segment for long clips). Embedding = 768-dim CLIP vector. Metadata = clip_id, timestamp.
- SQLite via SQLCipher: stored at `.prism/index.db`. Schema defined in `db/schema.sql`. WAL mode enabled for concurrent read/write. All tables and indexes from the schema in CLAUDE.md.
- Filesystem: thumbnails as WebP (320px wide), keyframes as JPEG (1280px wide), face crops as JPEG (128x128). Use consistent naming: `{clip_id}_thumb.webp`, `{clip_id}_kf_{n}.jpg`.

### Export
- `services/export.py` generates FCPXML (Final Cut Pro / DaVinci Resolve), EDL (universal), and CSV from the shot list.
- FCPXML must be valid XML that DaVinci Resolve 19 can import. Reference clip paths relative to the media folder root.
- EDL uses CMX3600 format with standard timecode.
- CSV includes: clip_id, file_path, duration, scene_caption, sharpness, exposure, stability, camera, resolution.

### Tests
- `test_auth.py`: valid token accepted, missing token → 401, invalid token → 401, expired token → 401.
- `test_security.py`: path traversal attempts → 400, symlink escape → 400, SQL injection in search → safe (parameterized), oversized query → 400.
- `test_pipeline.py`: single file through all 5 tracks, parallel execution timing, track failure isolation, manifest update.
- `test_search.py`: semantic-only, filter-only, hybrid, empty database, no results.

---

## Agent: DevOps

**Description:** Handles project configuration, build scripts, and development workflow.

**Scope:** Root directory, `scripts/`

**Rules:**
- `scripts/dev.sh`: starts the Python backend (`cd backend && uvicorn main:app --port 8420 --reload`) in background, then runs `npm run tauri dev` in foreground. Traps SIGINT to kill both processes.
- `scripts/seed_demo.py`: generates 20 fake clips with randomized metadata, quality scores, face clusters, and transcripts. Writes directly to `.prism/` in a demo directory. Used to populate the UI for development and screenshots without requiring real footage or AI models.
- `scripts/build.sh`: production build pipeline. (1) Bundle Python backend via PyInstaller into a single binary. (2) Copy binary to `src-tauri/binaries/`. (3) Run `npm run tauri build` to produce `.dmg` / `.msi` / `.AppImage`.
- `.gitignore` must include: `node_modules/`, `__pycache__/`, `.env`, `target/` (Rust), `.prism/`, `*.db`, `dist/`, `.next/`, `*.pyc`, `src-tauri/binaries/`.
- `README.md`: project overview, architecture diagram, prerequisites (Rust, Node 18+, Python 3.11+, Ollama, ffmpeg), dev setup instructions, usage guide, security model summary, export format docs.
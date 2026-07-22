# PRISM — Claude Code Project Context

## What Is This Project?

PRISM (Post-production Review & Intelligent Scene Manager) is a desktop application that automates the most time-consuming phase of filmmaking: footage review, organization, and pre-edit assembly. After a shoot, filmmakers return with hours of raw footage. Before editing can begin, every clip must be watched, logged, tagged, and organized — a process that takes 2-5 days on a real production. PRISM reduces it to minutes.

Point PRISM at a folder of raw footage. It processes every clip through five parallel AI analysis tracks. It builds a searchable index. You find any shot with natural language in seconds. Then you build a storyboard, assemble an edit, generate a dailies report, and export directly into DaVinci Resolve.

**This is a Tauri desktop app.** Filmmakers' media libraries are local. All AI models run locally via Ollama and direct Python libraries. No footage ever leaves the machine. No cloud. No API keys. NDA-safe by design.

## System Design Principles

### 1. Offline-First, Privacy-First
All AI models run locally. No network requests after install. Footage metadata stays on the machine. Non-negotiable.

### 2. Process Once, Query Forever
Ingestion is expensive (VLM, CLIP, Whisper, face detection). It happens once per clip. After that, every search, filter, and similarity lookup is a fast vector/SQL query. Design every storage layer for read speed.

### 3. Parallelism by Default
The five analysis tracks are independent. They run concurrently via a worker pool. Total ingestion time = slowest track, not the sum. A progress event bus pushes per-track updates to the UI via WebSocket.

### 4. Separation of Storage Concerns
- **ChromaDB** → vector embeddings (similarity search via HNSW)
- **SQLite/SQLCipher** → structured metadata (filtering, joining, sorting)
- **Filesystem** → thumbnails, keyframes, face crops, transcripts, waveforms (.prism/ sidecar)

### 5. Non-Destructive Sidecar Architecture
PRISM never modifies original footage. All data lives in a `.prism/` directory alongside the media. Delete it = files untouched. Same philosophy as `.git/`.

---

## Hardware Requirements

PRISM runs all AI models locally. This is a hard requirement — not a preference. The compute cost is real.

### Minimum Spec
- **macOS:** Apple Silicon M1+ with 16GB unified memory (M2/M3 recommended for comfortable ingestion speed)
- **Windows/Linux:** 16GB RAM + NVIDIA GPU with 8GB+ VRAM (RTX 3060 or better)
- **Storage:** SSD for the `.prism/` sidecar (HDD will bottleneck thumbnail/keyframe I/O)
- **Ollama installed** with LLaVA 1.6 7B pulled (`ollama pull llava`)

### Model Resource Usage

| Model | VRAM/RAM | Speed | Reliability |
|-------|----------|-------|-------------|
| OpenCLIP ViT-L/14 | ~2GB | ~0.3s/frame | Excellent — proven on 400M+ image-text pairs |
| LLaVA 1.6 7B (Ollama) | ~6GB | ~3-5s/frame | Good — descriptive, accurate captions but not cinematographically nuanced |
| Whisper large-v3 (cpp) | ~3GB | ~0.3x realtime | Excellent — near-cloud transcription quality |
| pyannote.audio | ~1GB | Fast | Good with 2-3 speakers, less reliable with 4+ |
| face_recognition (dlib) | CPU only | ~0.5s/frame | Good for clear faces, misses small/profile/shadowed faces |
| OpenCV (quality scoring) | CPU only | ~0.1s/frame | Perfect — deterministic, not ML |
| ffprobe / ExifTool | Negligible | Instant | Perfect — data parsing, not AI |

### Honest Capability Assessment

**What works great locally:** Semantic search via CLIP (the core feature), Whisper transcription, quality scoring, metadata extraction, color palette extraction, duplicate detection, audio event detection. These are either proven models or classical algorithms.

**What works well but not perfectly:** Face clustering (may create duplicate clusters across lighting conditions — build manual merge/split into the UI), speaker diarization (reliable for interviews, less so for group scenes), VLM scene captions (accurate but generic — describes what's visible, not how it's shot).

**What was intentionally excluded:** Pre-production storyboard image generation (would require Stable Diffusion/Flux, 6-12GB additional VRAM, 10-30s per frame — conflicts with lightweight local-first design). Shot type classification via VLM (unreliable — replaced with face bounding box size heuristic which is deterministic).

### Ingestion Time Estimates (on M2 MacBook Pro 16GB)
- **Per clip (60 seconds of footage):** ~15-25 seconds total across all 5 parallel tracks
- **100 clips (~2 hours of footage):** ~25-40 minutes
- **500 clips (~8 hours of footage):** ~2-3 hours (background process, UI stays responsive)

Ingestion is a one-time cost per clip. After processing, all searches and queries are instant (<50ms).

---

## Architecture — Three-Layer Desktop App

```
┌──────────────────────────────────────────────────────────┐
│  TAURI SHELL (Rust)                                       │
│  File dialogs, window mgmt, filesystem permissions,       │
│  OS keychain, Python sidecar spawn, session token gen     │
└──────────┬──────────────────────────────┬─────────────────┘
           │ IPC (invoke)                  │ spawn + token
┌──────────▼──────────────┐    ┌──────────▼─────────────────┐
│  REACT FRONTEND (TS)     │    │  PYTHON BACKEND (FastAPI)   │
│  Vite + Tailwind         │    │  Port 8420 on 127.0.0.1     │
│  5 views:                │◄──►│  AI pipeline, search,        │
│  • Clip Browser          │HTTP│  storage, export, storyboard │
│  • Timeline              │ +  │                               │
│  • Transcript            │ WS │  5 ingestion tracks           │
│  • Assembly              │    │  + extended analysis          │
│  • Storyboard            │    │  Hybrid search engine          │
└──────────────────────────┘    └───────────────────────────────┘
                                          │
                     ┌────────────────────┬┴──────────────────┐
                     │                    │                    │
               ┌─────▼─────┐      ┌──────▼──────┐    ┌───────▼──────┐
               │  ChromaDB  │      │   SQLite    │    │  Filesystem  │
               │  (vectors) │      │  (SQLCipher)│    │  (.prism/)   │
               └────────────┘      └─────────────┘    └──────────────┘
```

---

## The .prism/ Sidecar Directory

```
Media_Folder/
├── A001_C001.mp4                      ← ORIGINAL (never touched)
├── ...
└── .prism/
    ├── index.db                       ← SQLCipher: all structured metadata
    ├── chroma/                        ← ChromaDB: vector embeddings
    ├── thumbs/                        ← WebP thumbnails (320px wide)
    ├── keyframes/                     ← Scene-change keyframes (JPEG 1280px)
    ├── transcripts/                   ← Whisper JSON (word-level timestamps)
    ├── faces/                         ← Face crop cache per cluster
    │   ├── cluster_0/
    │   └── ...
    ├── waveforms/                     ← Audio waveform data (JSON)
    ├── color_palettes/                ← Extracted dominant colors (JSON)
    ├── storyboards/                   ← Saved storyboard projects (JSON)
    ├── luts/                          ← User-imported .cube LUT files
    ├── exports/                       ← Generated PDFs, FCPXML, EDL
    └── manifest.json                  ← Tracks processed files + checksums
```

---

## Ingestion Pipeline — 5 Parallel Tracks

All tracks run concurrently via ProcessPoolExecutor (CPU-bound) + ThreadPoolExecutor (I/O-bound). Each track is independent — no shared state during processing.

### Track 1: Visual Intelligence
- PySceneDetect → scene boundaries → extract keyframes
- Each keyframe → OpenCLIP ViT-L/14 → 768-dim embedding (proven model, 400M+ training pairs, excellent for semantic search)
- VLM (LLaVA 1.6 7B via Ollama) → scene description per segment (~3-5s per frame, but higher quality captions than Moondream2 which produces functional but generic descriptions)
- Shot type classification: derived from face detection bounding box size (face >40% frame = close-up, 15-40% = medium, <15% = wide, no face = establishing/b-roll). More reliable than VLM classification.
- **Output:** CLIP vectors (ChromaDB), scene captions + shot_type (SQLite), keyframes (filesystem)
- **Capability note:** CLIP embeddings are the primary search mechanism and work very well. VLM captions are supplementary context for the detail sidebar. Captions will be descriptive and accurate but not cinematographically nuanced — they describe what's visible, not how it's shot.

### Track 2: Audio Intelligence
- ffmpeg → extract audio track
- Whisper.cpp (large-v3, C++ port — 3-5x faster than Python Whisper) → word-level transcription with timestamps. Near-cloud quality, genuinely excellent.
- pyannote.audio → speaker diarization. Reliable with 2-3 speakers (the common filmmaking case — interviews, dialogue scenes). Gets shakier with 4+ speakers — may occasionally merge or split speakers.
- RMS + peak analysis → audio quality flags (classical DSP, not AI — extremely reliable)
- Audio event detection → claps (slate markers), silence, wind noise, music, room tone (spectral analysis + amplitude thresholds — classical signal processing, very reliable)
- **Output:** Transcripts (JSON), speaker labels, audio quality scores, event markers (SQLite)

### Track 3: Technical Quality Scoring (NOT AI — classical computer vision, 100% reliable)
- Laplacian variance → sharpness (0-100)
- Histogram spread → exposure (0-100)
- Optical flow magnitude → stability (0-100)
- Color histogram consistency → color drift score (0-100)
- **Output:** Per-clip quality scores (SQLite)
- **Capability note:** These are deterministic algorithms, not ML models. They produce consistent, meaningful scores. This is the most reliable track in the pipeline.

### Track 4: Face Intelligence
- face_recognition (dlib) → face detection in keyframes (~99.38% accuracy on standard benchmarks)
- 128-dim face encodings → DBSCAN clustering
- No training data needed — unsupervised grouping
- **Output:** Face clusters with timestamps + bounding boxes (SQLite + face crops in filesystem)
- **Capability note:** Works well for clear, front-facing and slight-angle shots (interviews, medium shots). Struggles with: extreme side profiles, heavy shadow on faces, very small faces in wide shots (<30px), motion blur. DBSCAN may create two clusters for the same person if lighting changes dramatically between clips (indoor tungsten vs outdoor daylight). Tune epsilon parameter to balance precision vs recall. Good enough to be useful, not good enough to trust blindly — users should be able to manually merge/split clusters in the UI.

### Track 5: Metadata Extraction
- ffprobe → codec, resolution, fps, duration, audio channels, color space, bitrate
- Pillow/ExifTool → camera, lens, focal length, ISO, GPS
- Filesystem → file size, creation date, path
- **Output:** Structured metadata rows (SQLite)

### Extended Analysis (runs after Track 1 completes)

#### Color Palette Extraction
- Extract 5-6 dominant colors per clip from keyframes using k-means clustering on pixel values
- Store as hex swatches in SQLite
- Enable "Find by Color" search and visual consistency filtering for montage assembly

#### Duplicate Detection
- Compare CLIP embeddings at similarity threshold 0.95+
- Group near-duplicates (same framing, different take)
- Present in groups — highest quality score highlighted as "best"

---

## Extended Features

### Smart Collections
Auto-updating saved queries. Rules defined as filter + semantic combinations: "Quality > 70 AND Person is Person A AND Shot Type is Close-up." Live — new clips matching the rules appear automatically after ingestion. Stored in SQLite as serialized rule definitions.

### Storyboard Generator (5th View)

Two modes:

**Post-Shoot Board:** Select clips → PRISM generates a grid of best keyframes (selected by highest sharpness, not first frame) with clip ID, VLM description, duration, and quality scores. Export as PDF for director review. This is what a DIT or assistant editor sends to the director at the end of the day — "here's what we got."

**Assembly Board:** The Assembly workspace's shot list rendered as visual cells. Each cell shows representative frame, shot description (from script), matched clip ID, and VLM caption side by side. Intent vs reality comparison. Director reviews and approves before editing begins. This becomes a presentation document — the filmmaker shows the storyboard to the client before cutting a single frame in Resolve.

**Note:** Pre-production storyboard generation (creating images from text descriptions) is intentionally excluded. It would require Stable Diffusion or Flux (~6-12GB VRAM, 10-30s per frame), which conflicts with the lightweight local-first principle. This is a Phase 2 consideration if demand exists.

Storyboard cells contain: keyframe image (16:9), shot number, scene heading, description, matched clip + duration, quality scores, and a notes field for director markup.

Interactive: click to play, drag to reorder, double-click description to edit, right-click to swap clip (PRISM suggests alternatives via vector similarity). Add transition notes between cells.

Export: PDF (print-ready white background), image sequence (PNGs), FCPXML (placeholder timeline for Resolve), animatic video (MP4 with hold durations for timing).

### Dailies Report
Auto-generated per shoot day. Contains: date, total runtime, total clips, clips per camera, quality distribution chart, top 10 highest-scoring clips as thumbnails, face appearance summary, flagged technical issues (out of focus, audio problems, exposure warnings), auto-generated storyboard of highlights. Export as clean PDF.

### LUT Preview
Toggle in toolbar: "LUT: None | Rec.709 | Custom..." Applies a lookup table to all thumbnails and keyframes in the browser for S-Log3 / flat-profile footage. Ships with built-in Rec.709 conversion for S-Log3. Users can import custom .cube files. LUT applied to display only — originals never touched. Stored in `.prism/luts/`.

### Waveform + Audio Event Detection
Visual waveform in clip detail sidebar using teal (Track 2 color). Flagged audio events marked as dots on the waveform: claps (slate markers → "likely good take"), wind noise, room tone, silence, music. Clap detection enables automated "best take" flagging.

### Marker / Note System
Press "M" anywhere a clip plays to drop a timestamped marker with a one-line note. Markers appear as colored ticks on progress bars, waveforms, and timeline blocks. Colors are user-selectable (Apple system colors: red, orange, yellow, green, blue, purple — same as Finder tags). Markers export into FCPXML as native markers in Resolve. Markers carry over to storyboard cells when clips are used.

### Watch Folder Mode
Configured in settings. PRISM monitors a directory for new files. When new clips appear (camera card dump), ingestion starts automatically in background. Clips appear in browser with fade-in animation as they finish processing. A tiny pulse indicator in the top bar shows active monitoring.

### Script Matching (Assembly V2)
Paste a screenplay or shot list document. PRISM parses scene headings (INT. OFFICE - DAY), action lines, and dialogue. For each scene, semantic search finds candidate clips. Dialogue lines match against Whisper transcripts. Split view: script on left, suggested clips on right. Drag matches into place. Export as FCPXML.

---

## Hybrid Search Architecture

### Semantic (ChromaDB)
Natural language → CLIP encoding → cosine similarity against all embeddings → ranked results.

### Filtered (SQLite)
`resolution = '4K' AND fps = 24 AND camera = 'Sony A6700'`

### Combined
ChromaDB returns top-100 by similarity → SQLite filters those IDs → ranked intersection.

### Color Search
k-means palette vectors enable "find clips with similar color mood" — separate from CLIP semantic search.

Endpoint: `POST /search`
```json
{
  "query": "sunset wide shot",
  "filters": { "resolution": "3840x2160", "quality_min": 70 },
  "color_similar_to": "clip_id_123",
  "top_k": 20
}
```

---

## Scalability Design

- **Lazy thumbnail loading:** Intersection Observer, only visible tiles render
- **Incremental ingestion:** SHA-256 checksum diffing against manifest.json
- **HNSW vector index:** O(log n) approximate nearest neighbor, <50ms at 10K clips
- **Virtual scrolling:** Only DOM nodes for visible items, LIMIT/OFFSET pagination
- **Background job queue:** UI stays responsive during ingestion
- **WAL mode:** Concurrent SQLite reads during writes

---

## Security Architecture

### Layer 1: Session Token
Tauri generates 32-byte random hex token on launch → passes to Python as CLI arg → React gets via IPC → every request includes `Authorization: Bearer <token>`. Rejects requests without valid token.

### Layer 2: Filesystem Sandboxing
Path validation on every filesystem operation. Resolve canonical path, reject `../` traversal, reject symlinks outside media root, reject system directories. Tauri capabilities scope filesystem access.

### Layer 3: SQLCipher Encryption
AES-256 encrypted database. Key stored in OS keychain (macOS Keychain / Windows Credential Manager) via Tauri secure storage plugin.

### Layer 4: Input Sanitization
Parameterized SQL everywhere. Search input length-limited (500 chars). WebSocket messages schema-validated.

### Layer 5: Audit Logging
Every search, export, ingest, and delete action logged to audit_log table.

---

## Design System Reference

### Color Architecture

The five logo colors are FUNCTIONAL — they only appear when displaying data from their respective track:

| Color | Hex | Track | Appears When |
|-------|-----|-------|-------------|
| Violet | `#9B8AFF` | Visual Intelligence | Similarity scores, scene descriptions, search results |
| Teal | `#5AC8C8` | Audio Intelligence | Transcripts, speaker labels, waveforms |
| Green | `#4ADE80` | Technical Scoring | Quality dots, score bars |
| Amber | `#F5A623` | Face Intelligence | Face cluster rings, person labels |
| Coral | `#FF6B6B` | Metadata / Alerts | Error states, unusable footage flags |

**Rule: Maximum 2 of the 5 track colors visible at any time.**

### UI Chrome (Apple System Grays)
- `#000000` — base background
- `#1C1C1E` — panels
- `#2C2C2E` — surfaces
- `#38383A` — borders (1px, subtle)
- `#48484A` — hover states
- `#0A84FF` — interactive blue (buttons, selection, active states — the ONLY accent in general UI)
- `#F5F5F7` — primary text
- `#A1A1A6` — secondary text
- `#6E6E73` — tertiary text

### Typography
Inter only. Hierarchy via weight: Semibold (600) for labels, Regular (400) for values, lighter for secondary. `font-variant-numeric: tabular-nums` for timecodes. No monospace except literal code. No ALL CAPS.

### Liquid Glass
Used on: top bar, search overlay (Spotlight-style), modals/popovers, collapsed sidebar hover peek.
NOT used on: permanent panels, clip cards, anything read for extended periods.
```css
background: rgba(28, 28, 30, 0.72);
backdrop-filter: blur(40px) saturate(180%);
border: 0.5px solid rgba(255, 255, 255, 0.08);
```

### Animations
Spring curves (ease-out), 200-300ms. Clip selection: 150ms border fade. Sidebar slide: 250ms spring. View switch: 200ms cross-fade. Thumbnail hover scrub: instant (no delay). All animations interruptible.

### Non-Negotiables
- No gradients in UI chrome
- No colored section headers
- No visible grid lines in clip browser
- No colored borders (only `#0A84FF` selection ring)
- Footage thumbnails are always the largest element
- Maximum 2 track colors visible simultaneously

---

## App Startup States

### State 1: First Launch (Onboarding)

Near-empty window. PRISM logo (five-ray fan) centered vertically, slightly above middle, at ~64px. Below: "PRISM" in Inter Semibold, then "Footage intelligence for filmmakers" in `text-secondary`.

Below that, a single clean setup card — not a multi-step wizard. Two settings only:

**Encryption passphrase** — text field. Placeholder: "Set a passphrase to protect your project data." Subtle note below: "Stored in your system keychain. PRISM never sees your passphrase again after setup." This becomes the SQLCipher key.

**Default LUT** — segmented control: None | Rec.709 (S-Log3) | Custom. Default "None." Custom opens a .cube file picker. One line: "Applied to thumbnails only. Your footage is never modified."

Single "Get Started" button in Apple blue. Click → card fades away → empty state. No email. No name. No terms of service. No workflow survey. Two settings, one button, done.

### State 2: Empty State (No Project Open)

What the user sees after onboarding and every launch with no folder loaded. Both sidebars are hidden — no left panel, no right panel. Just the top bar (PRISM logo, dimmed view tabs) and the center area.

Center content:

A large drop zone filling most of the screen. Subtle dashed border (1px, `#38383A`, 12px rounded corners, generous padding). Inside: folder icon in `text-tertiary`, text "Drop a folder to start" in `text-secondary`. Below: "or" in `text-tertiary`, then "Browse..." text button in Apple blue (triggers native Tauri folder picker).

Drag response: when a folder is dragged over the window, border brightens to `#0A84FF`, background gets faint blue tint (`#0A84FF08`), text changes to "Release to open." Transition is instant.

Below the drop zone: "Recent Projects" list (only if previous projects exist — hidden on first launch). Each row: folder name (primary text), path (secondary text), clip count, last opened date. Click to reopen. Subtle hover state. If a drive is disconnected, the row shows "Drive not connected" in `text-tertiary` with folder name dimmed. No red error, no modal.

### State 3: Project Loading (Transition to Active)

**Returning project** (`.prism/` exists): Load existing index, 1-2 seconds. Sidebars fade in, view tabs activate, clip grid populates with staggered fade-in (50ms delay per clip for first 20 visible, then rest appear at once). No loading spinner.

**New folder** (no `.prism/`): Brief interstitial card: "Found 248 video files" with two buttons: "Start Processing" (Apple blue, primary — begins ingestion, progress overlay slides up from bottom) and "Browse First" (secondary — shows raw file list with filenames, durations, sizes so they can verify it's the right folder before committing to full ingestion).

### What NOT To Do At Startup
- No splash screen. Apple apps don't have them. Show the window frame immediately.
- No "what's new" modal. Put update notes behind a settings icon dot.
- No tips, tours, or tooltip walkthroughs. Professional users don't need hand-holding.
- No "connect to cloud" or "sign in" prompts. There is no cloud.
- No loading bar while "checking for updates." The app is local. It opens instantly.
- No feature carousel. No testimonials. No promotional content of any kind.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest` | Start ingestion for a folder path |
| GET | `/ingest/status` | Pipeline progress (per file, per track) |
| POST | `/ingest/cancel` | Cancel running ingestion |
| POST | `/search` | Hybrid search (semantic + filtered + color) |
| GET | `/clips` | Paginated clip list with filters |
| GET | `/clips/{id}` | Full clip detail |
| GET | `/clips/{id}/thumbnail` | Serve thumbnail |
| GET | `/clips/{id}/keyframes` | List keyframe images |
| GET | `/clips/{id}/waveform` | Audio waveform data |
| GET | `/clips/{id}/palette` | Color palette swatches |
| GET | `/clips/{id}/similar` | Find similar clips (vector similarity) |
| GET | `/faces` | List all face clusters |
| GET | `/faces/{cluster_id}/clips` | Clips containing a face |
| GET | `/transcript/{clip_id}` | Full transcript with word timestamps |
| POST | `/markers` | Create a timestamped marker on a clip |
| GET | `/markers/{clip_id}` | Get all markers for a clip |
| GET | `/collections` | List smart collections |
| POST | `/collections` | Create smart collection (rule definition) |
| GET | `/collections/{id}/clips` | Clips matching collection rules |
| POST | `/storyboard` | Create new storyboard project |
| GET | `/storyboard/{id}` | Get storyboard with all cells |
| PUT | `/storyboard/{id}` | Update storyboard (reorder, edit cells) |
| POST | `/storyboard/{id}/generate` | Auto-generate from clips or script |
| GET | `/dailies/{date}` | Generate dailies report for a date |
| GET | `/duplicates` | List duplicate groups |
| POST | `/export/fcpxml` | Generate FCPXML from storyboard or assembly |
| POST | `/export/edl` | Generate EDL |
| POST | `/export/pdf` | Generate storyboard/dailies PDF |
| POST | `/export/animatic` | Generate animatic MP4 from storyboard |
| GET | `/luts` | List available LUTs |
| POST | `/luts/upload` | Upload custom .cube LUT |
| POST | `/luts/apply-preview` | Apply LUT to a thumbnail (returns modified image) |
| GET | `/watch` | Watch folder status |
| POST | `/watch/configure` | Set watch folder path + toggle |
| GET | `/ws/progress` | WebSocket: ingestion progress stream |
| GET | `/ws/watch` | WebSocket: watch folder new file events |
| GET | `/health` | Backend health check |

---

## Database Schema (SQLCipher)

```sql
CREATE TABLE clips (
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
    shot_type TEXT,
    has_dialogue BOOLEAN DEFAULT FALSE,
    sharpness_score INTEGER,
    exposure_score INTEGER,
    stability_score INTEGER,
    color_score INTEGER,
    audio_quality TEXT,
    dominant_colors TEXT,
    lut_applied TEXT,
    duplicate_group_id TEXT,
    is_best_in_group BOOLEAN DEFAULT FALSE,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_hash)
);

CREATE TABLE face_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT,
    representative_face_path TEXT,
    encoding BLOB,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE face_appearances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER REFERENCES face_clusters(id),
    clip_id TEXT REFERENCES clips(id),
    timestamp_seconds REAL,
    bbox_x INTEGER, bbox_y INTEGER,
    bbox_w INTEGER, bbox_h INTEGER,
    confidence REAL
);

CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id TEXT REFERENCES clips(id),
    speaker_label TEXT,
    start_time REAL,
    end_time REAL,
    text TEXT,
    confidence REAL
);

CREATE TABLE audio_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id TEXT REFERENCES clips(id),
    event_type TEXT NOT NULL,
    timestamp_seconds REAL,
    duration_seconds REAL,
    confidence REAL
);

CREATE TABLE markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id TEXT REFERENCES clips(id),
    timestamp_seconds REAL NOT NULL,
    note TEXT,
    color TEXT DEFAULT 'blue',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE smart_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rules TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE storyboards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mode TEXT DEFAULT 'post_shoot',
    cells TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE watch_config (
    id INTEGER PRIMARY KEY,
    folder_path TEXT,
    active BOOLEAN DEFAULT FALSE,
    last_scan TEXT
);

-- Performance indexes
CREATE INDEX idx_clips_hash ON clips(file_hash);
CREATE INDEX idx_clips_camera ON clips(camera);
CREATE INDEX idx_clips_resolution ON clips(resolution);
CREATE INDEX idx_clips_sharpness ON clips(sharpness_score);
CREATE INDEX idx_clips_shot_type ON clips(shot_type);
CREATE INDEX idx_clips_duplicate_group ON clips(duplicate_group_id);
CREATE INDEX idx_clips_created ON clips(created_at);
CREATE INDEX idx_face_appearances_cluster ON face_appearances(cluster_id);
CREATE INDEX idx_face_appearances_clip ON face_appearances(clip_id);
CREATE INDEX idx_transcripts_clip ON transcripts(clip_id);
CREATE INDEX idx_transcripts_text ON transcripts(text);
CREATE INDEX idx_audio_events_clip ON audio_events(clip_id);
CREATE INDEX idx_audio_events_type ON audio_events(event_type);
CREATE INDEX idx_markers_clip ON markers(clip_id);
```

---

## Repo Structure

```
prism/
├── CLAUDE.md
├── AGENTS.md
├── README.md
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── index.html
│
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── capabilities/default.json
│   └── src/
│       ├── main.rs
│       └── lib.rs
│
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── styles.css
│   ├── components/
│   │   ├── TopBar.tsx
│   │   ├── ViewSwitcher.tsx
│   │   ├── ClipBrowser.tsx
│   │   ├── ClipCard.tsx
│   │   ├── ClipDetail.tsx
│   │   ├── SearchBar.tsx
│   │   ├── FilterPanel.tsx
│   │   ├── FaceSidebar.tsx
│   │   ├── TimelineView.tsx
│   │   ├── TranscriptView.tsx
│   │   ├── AssemblyWorkspace.tsx
│   │   ├── StoryboardView.tsx
│   │   ├── StoryboardCell.tsx
│   │   ├── DailiesReport.tsx
│   │   ├── ProgressOverlay.tsx
│   │   ├── SmartCollectionEditor.tsx
│   │   ├── DuplicateGroups.tsx
│   │   ├── WaveformDisplay.tsx
│   │   ├── ColorPalette.tsx
│   │   ├── MarkerPopover.tsx
│   │   ├── LutSelector.tsx
│   │   ├── WatchFolderIndicator.tsx
│   │   ├── ScoreBar.tsx
│   │   └── ExportDialog.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useClipLibrary.ts
│   │   ├── useIngestionProgress.ts
│   │   ├── useVirtualScroll.ts
│   │   ├── useStoryboard.ts
│   │   └── useWatchFolder.ts
│   ├── lib/
│   │   ├── api.ts
│   │   ├── tauri.ts
│   │   ├── types.ts
│   │   └── constants.ts
│   └── assets/
│       └── prism-logo.svg
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── requirements.txt
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── scanner.py
│   │   ├── visual.py
│   │   ├── audio.py
│   │   ├── technical.py
│   │   ├── faces.py
│   │   ├── metadata.py
│   │   ├── color_palette.py
│   │   └── duplicates.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   ├── metadata_store.py
│   │   ├── search.py
│   │   ├── export.py
│   │   ├── storyboard.py
│   │   ├── dailies.py
│   │   ├── lut.py
│   │   ├── markers.py
│   │   ├── collections.py
│   │   ├── watch.py
│   │   └── ws_manager.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── search.py
│   │   ├── clips.py
│   │   ├── faces.py
│   │   ├── transcript.py
│   │   ├── markers.py
│   │   ├── collections.py
│   │   ├── storyboard.py
│   │   ├── dailies.py
│   │   ├── duplicates.py
│   │   ├── luts.py
│   │   ├── watch.py
│   │   ├── export.py
│   │   └── stream.py
│   ├── db/
│   │   └── schema.sql
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_search.py
│       ├── test_pipeline.py
│       ├── test_auth.py
│       ├── test_security.py
│       ├── test_storyboard.py
│       └── test_export.py
│
├── docs/
│   ├── design-system.md
│   └── assets/
│       ├── prism-logo.svg
│       ├── prism-icon-1024.png
│       └── prism-screenshot.png
│
└── scripts/
    ├── dev.sh
    ├── seed_demo.py
    └── build.sh
```

---

## Coding Conventions

### Python (backend/)
- Python 3.11+, type hints everywhere, Pydantic v2 for all models
- Async FastAPI with uvicorn, parameterized SQL everywhere
- Logging: `[PIPELINE:T1]`, `[SEARCH]`, `[AUTH]`, `[WATCH]`
- Tests: pytest + httpx.AsyncClient

### TypeScript (src/)
- Strict mode, no `any`, functional components with hooks
- Tailwind CSS only, no CSS modules
- Virtual scrolling for lists >100 items
- `font-variant-numeric: tabular-nums` for timecodes

### Rust (src-tauri/)
- Minimal — only Tauri commands, sidecar spawn, keychain ops
- `Result<T, String>` returns, never `unwrap()` in production

### Git
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `security:`
- Never commit: `.prism/`, `node_modules/`, `__pycache__/`, `.env`, `target/`, model weights

---

## Current Status

- [x] Project scaffold (Tauri + React + Python)
- [x] Security: token auth, path validation, SQLCipher
- [x] Pipeline: orchestrator, scanner, worker pool
- [x] Track 1: Visual (PySceneDetect + OpenCLIP + VLM)
- [x] Track 2: Audio (Whisper.cpp + pyannote + event detection)
- [x] Track 3: Technical (OpenCV quality scoring)
- [x] Track 4: Face (face_recognition + DBSCAN)
- [x] Track 5: Metadata (ffprobe + ExifTool)
- [x] Color Palette Extraction
- [x] Duplicate Detection
- [x] Storage: ChromaDB + SQLCipher + sidecar
- [x] Hybrid Search Engine
- [x] Smart Collections
- [x] Marker / Note System
- [x] LUT Preview
- [x] Watch Folder Mode
- [x] UI: Clip Browser with virtual scroll + hover scrub
- [x] UI: Timeline View
- [x] UI: Transcript View with click-to-jump
- [x] UI: Assembly Workspace with script matching
- [x] UI: Storyboard View (2 modes + export)
- [x] Dailies Report Generator
- [x] Export: FCPXML, EDL, CSV, PDF, Animatic MP4
- [ ] Testing: security, pipeline, search, storyboard, export
import argparse
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import TokenAuthMiddleware
from config import settings
from services.export import ExportService
from services.metadata_store import MetadataStore
from services.search import HybridSearchEngine
from services.vector_store import VectorStore
from services.ws_manager import WebSocketManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("prism")

_store: MetadataStore | None = None
_vector_store: VectorStore | None = None
_search_engine: HybridSearchEngine | None = None
_ws_manager = WebSocketManager()
_orchestrator = None
_export_service = ExportService()
_prism_dir: Path | None = None


def get_store() -> MetadataStore | None:
    return _store


def get_vector_store() -> VectorStore | None:
    return _vector_store


def get_search_engine() -> HybridSearchEngine | None:
    return _search_engine


def get_ws_manager() -> WebSocketManager:
    return _ws_manager


def get_orchestrator():
    return _orchestrator


def get_export_service() -> ExportService:
    return _export_service


def get_prism_dir() -> Path | None:
    return _prism_dir


def init_project(folder_path: str, db_key: str | None = None) -> None:
    global _store, _vector_store, _search_engine, _orchestrator, _prism_dir

    media_root = Path(folder_path)
    _prism_dir = media_root / ".prism"
    _prism_dir.mkdir(parents=True, exist_ok=True)

    db_path = _prism_dir / "index.db"
    _store = MetadataStore(db_path, encryption_key=db_key)

    chroma_path = str(_prism_dir / "chroma")
    _vector_store = VectorStore(chroma_path)

    _search_engine = HybridSearchEngine(_vector_store, _store)

    from pipeline.orchestrator import PipelineOrchestrator
    _orchestrator = PipelineOrchestrator(
        media_root=media_root,
        metadata_store=_store,
        vector_store=_vector_store,
        ws_manager=_ws_manager,
    )

    logger.info("Project initialized: %s", folder_path)


def create_app(token: str | None = None) -> FastAPI:
    app = FastAPI(title="PRISM Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if token:
        app.add_middleware(TokenAuthMiddleware, token=token)

    from routers import (
        ingest, clips, search, faces, transcript,
        markers, collections, storyboard, dailies,
        duplicates, luts, watch, export, stream,
    )

    app.include_router(ingest.router)
    app.include_router(clips.router)
    app.include_router(search.router)
    app.include_router(faces.router)
    app.include_router(transcript.router)
    app.include_router(markers.router)
    app.include_router(collections.router)
    app.include_router(storyboard.router)
    app.include_router(dailies.router)
    app.include_router(duplicates.router)
    app.include_router(luts.router)
    app.include_router(watch.router)
    app.include_router(export.router)
    app.include_router(stream.router)

    @app.get("/health")
    async def health():
        clip_count = _store.count_clips() if _store else 0
        return {
            "status": "ok",
            "version": "0.1.0",
            "project_loaded": _store is not None,
            "clip_count": clip_count,
        }

    @app.post("/project/open")
    async def open_project(data: dict):
        folder_path = data.get("folder_path")
        if not folder_path or not Path(folder_path).is_dir():
            return {"error": "Invalid folder path"}
        init_project(folder_path, db_key=data.get("db_key"))
        return {"status": "ok", "folder": folder_path}

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="PRISM Backend")
    parser.add_argument("--token", type=str, default=None, help="Session auth token")
    parser.add_argument("--db-key", type=str, default=None, help="SQLCipher encryption key")
    parser.add_argument("--project", type=str, default=None, help="Auto-open project folder")
    args = parser.parse_args()

    if args.project:
        init_project(args.project, db_key=args.db_key)

    app = create_app(token=args.token)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()

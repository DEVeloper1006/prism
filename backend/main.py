import argparse
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import TokenAuthMiddleware
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("prism")


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

    # TODO: mount routers for ingest, clips, search, faces, transcript, export

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="PRISM Backend")
    parser.add_argument("--token", type=str, default=None, help="Session auth token")
    parser.add_argument("--db-key", type=str, default=None, help="SQLCipher encryption key")
    args = parser.parse_args()

    app = create_app(token=args.token)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()

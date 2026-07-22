"""Ingestion endpoints."""

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException

from models.schemas import IngestJob, IngestRequest

router = APIRouter(tags=["ingest"])


@router.post("/ingest")
async def start_ingest(req: IngestRequest):
    from main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="No project loaded")

    folder = Path(req.folder_path)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail="Invalid folder path")

    asyncio.create_task(orch.ingest(folder))
    return {"status": "started", "folder": str(folder)}


@router.get("/ingest/status")
async def ingest_status():
    from main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        return IngestJob(folder_path="", status="idle")
    return orch.get_status()


@router.post("/ingest/cancel")
async def cancel_ingest():
    from main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    await orch.cancel()
    return {"status": "cancelling"}

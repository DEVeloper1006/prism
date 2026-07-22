"""LUT management endpoints."""

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

router = APIRouter(tags=["luts"])


@router.get("/luts")
async def list_luts():
    from main import get_prism_dir

    prism_dir = get_prism_dir()
    if prism_dir is None:
        return []
    lut_dir = prism_dir / "luts"
    if not lut_dir.exists():
        return []
    return [
        {"name": p.stem, "path": str(p)}
        for p in sorted(lut_dir.glob("*.cube"))
    ]


@router.post("/luts/upload")
async def upload_lut(file: UploadFile = File(...)):
    from main import get_prism_dir

    prism_dir = get_prism_dir()
    if prism_dir is None:
        raise HTTPException(status_code=503, detail="No project loaded")

    if not file.filename or not file.filename.endswith(".cube"):
        raise HTTPException(status_code=400, detail="Only .cube LUT files accepted")

    lut_dir = prism_dir / "luts"
    lut_dir.mkdir(parents=True, exist_ok=True)
    dest = lut_dir / file.filename

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"name": dest.stem, "path": str(dest)}

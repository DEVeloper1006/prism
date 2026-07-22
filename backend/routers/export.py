"""Export endpoints for FCPXML, EDL, PDF."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from models.schemas import ExportRequest

router = APIRouter(tags=["export"])


@router.post("/export/fcpxml")
async def export_fcpxml(req: ExportRequest):
    from main import get_store, get_export_service

    store = get_store()
    export_svc = get_export_service()
    if store is None or export_svc is None:
        raise HTTPException(status_code=503, detail="No project loaded")

    clips = []
    for clip_id in req.clip_ids:
        clip = store.get_clip(clip_id)
        if clip:
            clips.append(clip)

    content = export_svc.to_fcpxml(clips)
    store.log_action("export_fcpxml", f"{len(clips)} clips")
    return Response(content=content, media_type="application/xml",
                    headers={"Content-Disposition": "attachment; filename=prism_export.fcpxml"})


@router.post("/export/edl")
async def export_edl(req: ExportRequest):
    from main import get_store, get_export_service

    store = get_store()
    export_svc = get_export_service()
    if store is None or export_svc is None:
        raise HTTPException(status_code=503, detail="No project loaded")

    clips = []
    for clip_id in req.clip_ids:
        clip = store.get_clip(clip_id)
        if clip:
            clips.append(clip)

    content = export_svc.to_edl(clips)
    store.log_action("export_edl", f"{len(clips)} clips")
    return Response(content=content, media_type="text/plain",
                    headers={"Content-Disposition": "attachment; filename=prism_export.edl"})


@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    return {"status": "not_implemented", "detail": "PDF export requires reportlab"}

"""Dailies report endpoint."""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["dailies"])


@router.get("/dailies/{date}")
async def get_dailies(date: str):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")

    clips = store.list_clips(
        filters={"date_from": f"{date}T00:00:00", "date_to": f"{date}T23:59:59"}
    )

    total_duration = sum(c.get("duration_seconds") or 0 for c in clips)
    cameras = {}
    for c in clips:
        cam = c.get("camera") or "Unknown"
        cameras[cam] = cameras.get(cam, 0) + 1

    quality_dist = {"good": 0, "warning": 0, "poor": 0}
    for c in clips:
        score = c.get("sharpness_score") or 0
        if score >= 70:
            quality_dist["good"] += 1
        elif score >= 40:
            quality_dist["warning"] += 1
        else:
            quality_dist["poor"] += 1

    top_clips = sorted(clips, key=lambda c: c.get("sharpness_score") or 0, reverse=True)[:10]

    return {
        "date": date,
        "total_clips": len(clips),
        "total_duration_seconds": total_duration,
        "cameras": cameras,
        "quality_distribution": quality_dist,
        "top_clips": top_clips,
    }

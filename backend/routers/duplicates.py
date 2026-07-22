"""Duplicate detection endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["duplicates"])


@router.get("/duplicates")
async def list_duplicates():
    from main import get_store

    store = get_store()
    if store is None:
        return []
    return store.get_duplicate_groups()

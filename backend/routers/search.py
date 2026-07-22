"""Search endpoint."""

from fastapi import APIRouter

from models.schemas import SearchQuery

router = APIRouter(tags=["search"])


@router.post("/search")
async def search(query: SearchQuery):
    from main import get_search_engine

    engine = get_search_engine()
    if engine is None:
        return []

    filters = query.filters.model_dump(exclude_none=True) if query.filters else None
    return engine.search(
        query=query.query,
        filters=filters,
        color_similar_to=query.color_similar_to,
        top_k=query.top_k,
    )

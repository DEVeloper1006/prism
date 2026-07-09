"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field


class ClipResponse(BaseModel):
    id: str
    file_path: str
    file_hash: str
    duration_seconds: float | None = None
    resolution: str | None = None
    fps: float | None = None
    codec: str | None = None
    color_space: str | None = None
    audio_channels: int | None = None
    camera: str | None = None
    lens: str | None = None
    focal_length: str | None = None
    iso: int | None = None
    gps_lat: float | None = None
    gps_lon: float | None = None
    file_size_bytes: int | None = None
    created_at: str | None = None
    scene_caption: str | None = None
    has_dialogue: bool = False
    sharpness_score: int | None = None
    exposure_score: int | None = None
    stability_score: int | None = None
    color_score: int | None = None
    audio_quality: str | None = None
    ingested_at: str | None = None


class SearchFilters(BaseModel):
    resolution: str | None = None
    camera: str | None = None
    fps: float | None = None
    quality_min: int | None = None
    has_dialogue: bool | None = None
    date_from: str | None = None
    date_to: str | None = None


class SearchQuery(BaseModel):
    query: str | None = None
    filters: SearchFilters | None = None
    top_k: int = Field(default=20, ge=1, le=100)


class IngestRequest(BaseModel):
    folder_path: str


class IngestJob(BaseModel):
    folder_path: str
    total_files: int = 0
    processed_files: int = 0
    status: str = "pending"


class FaceClusterResponse(BaseModel):
    id: int
    label: str | None = None
    representative_face_path: str | None = None
    count: int = 0


class TranscriptSegment(BaseModel):
    id: int
    clip_id: str
    speaker_label: str | None = None
    start_time: float
    end_time: float
    text: str
    confidence: float | None = None

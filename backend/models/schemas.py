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
    shot_type: str | None = None
    has_dialogue: bool = False
    sharpness_score: int | None = None
    exposure_score: int | None = None
    stability_score: int | None = None
    color_score: int | None = None
    audio_quality: str | None = None
    dominant_colors: str | None = None
    lut_applied: str | None = None
    duplicate_group_id: str | None = None
    is_best_in_group: bool = False
    ingested_at: str | None = None


class SearchFilters(BaseModel):
    resolution: str | None = None
    camera: str | None = None
    fps: float | None = None
    quality_min: int | None = None
    has_dialogue: bool | None = None
    shot_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class SearchQuery(BaseModel):
    query: str | None = None
    filters: SearchFilters | None = None
    color_similar_to: str | None = None
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


class AudioEventResponse(BaseModel):
    id: int
    clip_id: str
    event_type: str
    timestamp_seconds: float
    duration_seconds: float | None = None
    confidence: float | None = None


class MarkerCreate(BaseModel):
    clip_id: str
    timestamp_seconds: float
    note: str | None = None
    color: str = "blue"


class MarkerResponse(BaseModel):
    id: int
    clip_id: str
    timestamp_seconds: float
    note: str | None = None
    color: str = "blue"
    created_at: str | None = None


class CollectionCreate(BaseModel):
    name: str
    rules: str


class CollectionResponse(BaseModel):
    id: int
    name: str
    rules: str
    created_at: str | None = None
    updated_at: str | None = None


class StoryboardCreate(BaseModel):
    name: str
    mode: str = "post_shoot"
    cells: str = "[]"


class StoryboardResponse(BaseModel):
    id: int
    name: str
    mode: str
    cells: str
    created_at: str | None = None
    updated_at: str | None = None


class StoryboardUpdate(BaseModel):
    name: str | None = None
    cells: str | None = None


class WatchConfigRequest(BaseModel):
    folder_path: str | None = None
    active: bool = False


class WatchConfigResponse(BaseModel):
    folder_path: str | None = None
    active: bool = False
    last_scan: str | None = None


class DuplicateGroupResponse(BaseModel):
    group_id: str
    clips: list[ClipResponse]
    best_clip_id: str | None = None


class ExportRequest(BaseModel):
    clip_ids: list[str] = []
    storyboard_id: int | None = None

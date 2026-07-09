export interface Clip {
  id: string;
  file_path: string;
  file_hash: string;
  duration_seconds: number | null;
  resolution: string | null;
  fps: number | null;
  codec: string | null;
  color_space: string | null;
  audio_channels: number | null;
  camera: string | null;
  lens: string | null;
  focal_length: string | null;
  iso: number | null;
  gps_lat: number | null;
  gps_lon: number | null;
  file_size_bytes: number | null;
  created_at: string | null;
  scene_caption: string | null;
  has_dialogue: boolean;
  sharpness_score: number | null;
  exposure_score: number | null;
  stability_score: number | null;
  color_score: number | null;
  audio_quality: string | null;
  ingested_at: string;
}

export interface FaceCluster {
  id: number;
  label: string | null;
  representative_face_path: string | null;
  count: number;
}

export interface TranscriptSegment {
  id: number;
  clip_id: string;
  speaker_label: string | null;
  start_time: number;
  end_time: number;
  text: string;
  confidence: number | null;
}

export interface SearchQuery {
  query?: string;
  filters?: SearchFilters;
  top_k?: number;
}

export interface SearchFilters {
  resolution?: string;
  camera?: string;
  fps?: number;
  quality_min?: number;
  has_dialogue?: boolean;
  date_from?: string;
  date_to?: string;
}

export interface IngestJob {
  folder_path: string;
  total_files: number;
  processed_files: number;
  status: "pending" | "running" | "completed" | "cancelled" | "error";
}

export interface ProgressEvent {
  clip_id: string;
  track: string;
  status: "started" | "completed" | "error";
  progress: number;
  message?: string;
}

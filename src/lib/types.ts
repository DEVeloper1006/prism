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
  shot_type: string | null;
  has_dialogue: boolean;
  sharpness_score: number | null;
  exposure_score: number | null;
  stability_score: number | null;
  color_score: number | null;
  audio_quality: string | null;
  dominant_colors: string | null;
  lut_applied: string | null;
  duplicate_group_id: string | null;
  is_best_in_group: boolean;
  ingested_at: string;
}

export interface FaceCluster {
  id: number;
  label: string | null;
  representative_face_path: string | null;
  count: number;
}

export interface FaceAppearance {
  id: number;
  cluster_id: number;
  clip_id: string;
  timestamp_seconds: number;
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  confidence: number;
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

export interface AudioEvent {
  id: number;
  clip_id: string;
  event_type: string;
  timestamp_seconds: number;
  duration_seconds: number | null;
  confidence: number | null;
}

export interface Marker {
  id: number;
  clip_id: string;
  timestamp_seconds: number;
  note: string | null;
  color: string;
  created_at: string;
}

export interface SmartCollection {
  id: number;
  name: string;
  rules: string;
  created_at: string;
  updated_at: string;
}

export interface Storyboard {
  id: number;
  name: string;
  mode: "post_shoot" | "assembly";
  cells: string;
  created_at: string;
  updated_at: string;
}

export interface StoryboardCell {
  clip_id: string;
  shot_number: number;
  description: string;
  notes: string;
  keyframe_path: string | null;
  duration_seconds: number | null;
  quality_scores: {
    sharpness: number | null;
    exposure: number | null;
    stability: number | null;
  };
}

export interface SearchQuery {
  query?: string;
  filters?: SearchFilters;
  color_similar_to?: string;
  top_k?: number;
}

export interface SearchFilters {
  resolution?: string;
  camera?: string;
  fps?: number;
  quality_min?: number;
  has_dialogue?: boolean;
  shot_type?: string;
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

export interface DuplicateGroup {
  group_id: string;
  clips: Clip[];
  best_clip_id: string;
}

export interface WatchConfig {
  folder_path: string | null;
  active: boolean;
  last_scan: string | null;
}

export type View = "browser" | "timeline" | "transcript" | "assembly" | "storyboard";

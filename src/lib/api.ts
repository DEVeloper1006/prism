import { API_URL } from "./constants";
import type {
  Clip, SearchQuery, FaceCluster, TranscriptSegment,
  Marker, SmartCollection, Storyboard, WatchConfig,
  DuplicateGroup,
} from "./types";

let sessionToken = "";

export function setToken(token: string) {
  sessionToken = token;
}

function headers(): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${sessionToken}`,
  };
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: headers() });
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`POST ${path}: ${res.status}`);
  return res.json();
}

async function put<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "PUT",
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`PUT ${path}: ${res.status}`);
  return res.json();
}

export async function healthCheck(): Promise<{ status: string; project_loaded: boolean; clip_count: number }> {
  return get("/health");
}

export async function openProject(folderPath: string): Promise<{ status: string }> {
  return post("/project/open", { folder_path: folderPath });
}

export async function startIngest(folderPath: string): Promise<void> {
  await post("/ingest", { folder_path: folderPath });
}

export async function getIngestStatus() {
  return get<{ status: string; total_files: number; processed_files: number }>("/ingest/status");
}

export async function cancelIngest(): Promise<void> {
  await post("/ingest/cancel");
}

export async function getClips(offset = 0, limit = 50): Promise<Clip[]> {
  return get(`/clips?offset=${offset}&limit=${limit}`);
}

export async function getClip(id: string): Promise<Clip> {
  return get(`/clips/${encodeURIComponent(id)}`);
}

export function getClipThumbnailUrl(id: string): string {
  return `${API_URL}/clips/${encodeURIComponent(id)}/thumbnail`;
}

export async function getClipKeyframes(id: string): Promise<string[]> {
  return get(`/clips/${encodeURIComponent(id)}/keyframes`);
}

export async function getClipPalette(id: string): Promise<string[]> {
  return get(`/clips/${encodeURIComponent(id)}/palette`);
}

export async function getSimilarClips(id: string): Promise<Array<{ clip_id: string; score: number }>> {
  return get(`/clips/${encodeURIComponent(id)}/similar`);
}

export async function search(query: SearchQuery): Promise<Clip[]> {
  return post("/search", query);
}

export async function getFaces(): Promise<FaceCluster[]> {
  return get("/faces");
}

export async function getFaceClips(clusterId: number): Promise<Clip[]> {
  return get(`/faces/${clusterId}/clips`);
}

export async function getTranscript(clipId: string): Promise<TranscriptSegment[]> {
  return get(`/transcript/${encodeURIComponent(clipId)}`);
}

export async function createMarker(clipId: string, timestampSeconds: number, note?: string, color?: string) {
  return post("/markers", { clip_id: clipId, timestamp_seconds: timestampSeconds, note, color });
}

export async function getMarkers(clipId: string): Promise<Marker[]> {
  return get(`/markers/${encodeURIComponent(clipId)}`);
}

export async function getCollections(): Promise<SmartCollection[]> {
  return get("/collections");
}

export async function createCollection(name: string, rules: string) {
  return post("/collections", { name, rules });
}

export async function getCollectionClips(collectionId: number): Promise<Clip[]> {
  return get(`/collections/${collectionId}/clips`);
}

export async function createStoryboard(name: string, mode = "post_shoot") {
  return post<{ id: number }>("/storyboard", { name, mode, cells: "[]" });
}

export async function getStoryboard(id: number): Promise<Storyboard> {
  return get(`/storyboard/${id}`);
}

export async function updateStoryboard(id: number, data: { name?: string; cells?: string }) {
  return put(`/storyboard/${id}`, data);
}

export async function getDailies(date: string) {
  return get(`/dailies/${date}`);
}

export async function getDuplicates(): Promise<DuplicateGroup[]> {
  return get("/duplicates");
}

export async function getWatchStatus(): Promise<WatchConfig> {
  return get("/watch");
}

export async function configureWatch(folderPath: string | null, active: boolean) {
  return post("/watch/configure", { folder_path: folderPath, active });
}

export async function exportFcpxml(clipIds: string[]) {
  const res = await fetch(`${API_URL}/export/fcpxml`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ clip_ids: clipIds }),
  });
  return res.text();
}

export async function exportEdl(clipIds: string[]) {
  const res = await fetch(`${API_URL}/export/edl`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ clip_ids: clipIds }),
  });
  return res.text();
}

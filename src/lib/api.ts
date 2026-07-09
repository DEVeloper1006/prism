import { API_URL } from "./constants";
import type { Clip, SearchQuery } from "./types";

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

export async function healthCheck(): Promise<boolean> {
  const res = await fetch(`${API_URL}/health`, { headers: headers() });
  return res.ok;
}

export async function startIngest(folderPath: string): Promise<void> {
  await fetch(`${API_URL}/ingest`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ folder_path: folderPath }),
  });
}

export async function getClips(page = 0, pageSize = 50): Promise<Clip[]> {
  const res = await fetch(
    `${API_URL}/clips?offset=${page * pageSize}&limit=${pageSize}`,
    { headers: headers() },
  );
  return res.json();
}

export async function getClip(id: string): Promise<Clip> {
  const res = await fetch(`${API_URL}/clips/${encodeURIComponent(id)}`, {
    headers: headers(),
  });
  return res.json();
}

export async function search(query: SearchQuery): Promise<Clip[]> {
  const res = await fetch(`${API_URL}/search`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(query),
  });
  return res.json();
}

import { invoke } from "@tauri-apps/api/core";

export async function getToken(): Promise<string> {
  return invoke<string>("get_token");
}

export async function openFolder(): Promise<string | null> {
  return invoke<string | null>("open_folder");
}

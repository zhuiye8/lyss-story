import type {
  ChapterDetail,
  ChapterSummary,
  GenerationStatus,
  StoryBible,
  StoryResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function createStory(
  theme: string,
  requirements: string = ""
): Promise<StoryResponse> {
  return fetchJson(`${API_BASE}/stories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, requirements }),
  });
}

export async function listStories(): Promise<StoryResponse[]> {
  return fetchJson(`${API_BASE}/stories`);
}

export async function getStory(storyId: string): Promise<StoryResponse> {
  return fetchJson(`${API_BASE}/stories/${storyId}`);
}

export async function getStoryBible(storyId: string): Promise<StoryBible> {
  return fetchJson(`${API_BASE}/stories/${storyId}/bible`);
}

export async function listChapters(
  storyId: string
): Promise<ChapterSummary[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/chapters`);
}

export async function getChapter(
  storyId: string,
  num: number
): Promise<ChapterDetail> {
  return fetchJson(`${API_BASE}/stories/${storyId}/chapters/${num}`);
}

export async function triggerGeneration(
  storyId: string
): Promise<{ message: string; chapter_num: number }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/generate`, {
    method: "POST",
  });
}

export async function getStatus(storyId: string): Promise<GenerationStatus> {
  return fetchJson(`${API_BASE}/stories/${storyId}/control/status`);
}

export interface StageProgress {
  name: string;
  label: string;
  status: string; // pending / running / done / error
  detail: string;
  duration_ms: number;
}

export interface GenerationProgressData {
  story_id: string;
  chapter_num: number;
  elapsed_seconds: number;
  current_stage: string | null;
  current_stage_label: string | null;
  error: string | null;
  stages: StageProgress[];
}

export async function getProgress(storyId: string): Promise<GenerationProgressData> {
  return fetchJson(`${API_BASE}/stories/${storyId}/control/progress`);
}

import type {
  CharacterWithArc,
  ChapterDetail,
  ChapterSummary,
  ChapterVersionDetail,
  ChapterVersionSummary,
  GenerationStatus,
  KnowledgeGraphData,
  StoryBible,
  StoryEvent,
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
  requirements: string = "",
  title: string = ""
): Promise<StoryResponse> {
  return fetchJson(`${API_BASE}/stories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, requirements, title }),
  });
}

export async function importOutline(
  storyId: string,
  rawText: string,
  title: string = ""
): Promise<{ story_id: string; title: string; status: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/import-outline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText, title }),
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
  storyId: string,
  wordCount?: number
): Promise<{ message: string; chapter_num: number; word_count?: number }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(wordCount ? { word_count: wordCount } : {}),
  });
}

export async function getStatus(storyId: string): Promise<GenerationStatus> {
  return fetchJson(`${API_BASE}/stories/${storyId}/control/status`);
}

export async function publishStory(
  storyId: string,
  publish: boolean
): Promise<void> {
  await fetchJson(`${API_BASE}/stories/${storyId}/publish`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ publish }),
  });
}

export async function publishChapter(
  storyId: string,
  chapterNum: number,
  publish: boolean
): Promise<void> {
  await fetchJson(`${API_BASE}/stories/${storyId}/chapters/${chapterNum}/publish`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ publish }),
  });
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

export async function regenerateChapter(
  storyId: string,
  chapterNum: number,
  feedback: string
): Promise<{ message: string; chapter_num: number }> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/regenerate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback }),
    }
  );
}

export async function listChapterVersions(
  storyId: string,
  chapterNum: number
): Promise<ChapterVersionSummary[]> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/versions`
  );
}

export async function getChapterVersion(
  storyId: string,
  chapterNum: number,
  versionId: number
): Promise<ChapterVersionDetail> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/versions/${versionId}`
  );
}

export async function restoreChapterVersion(
  storyId: string,
  chapterNum: number,
  versionId: number
): Promise<{ message: string; version_num: number }> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/restore/${versionId}`,
    { method: "POST" }
  );
}

// --- Visualization APIs ---

export async function getCharacters(
  storyId: string
): Promise<CharacterWithArc[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/characters`);
}

export async function getKnowledgeGraph(
  storyId: string,
  asOfChapter?: number
): Promise<KnowledgeGraphData> {
  const url = new URL(`${API_BASE}/stories/${storyId}/knowledge-graph`);
  if (asOfChapter != null) url.searchParams.set("as_of_chapter", String(asOfChapter));
  return fetchJson(url.toString());
}

export async function getEvents(storyId: string): Promise<StoryEvent[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/events`);
}

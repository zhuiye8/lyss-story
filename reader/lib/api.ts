import type { Book, BookDetail, ChapterContent } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/public";

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function listBooks(): Promise<Book[]> {
  return fetchJson(`${API_BASE}/books`);
}

export async function getBook(bookId: string): Promise<BookDetail> {
  return fetchJson(`${API_BASE}/books/${bookId}`);
}

export async function readChapter(bookId: string, chapterNum: number): Promise<ChapterContent> {
  return fetchJson(`${API_BASE}/books/${bookId}/chapters/${chapterNum}`);
}

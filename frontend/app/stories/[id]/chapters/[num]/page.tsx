"use client";

import { useCallback, useEffect, useState, use } from "react";
import Link from "next/link";
import ChapterReader from "@/components/ChapterReader";
import ChapterVersionPanel from "@/components/ChapterVersionPanel";
import { getChapter } from "@/lib/api";
import type { ChapterDetail } from "@/types";

export default function ChapterPage({
  params,
}: {
  params: Promise<{ id: string; num: string }>;
}) {
  const { id: storyId, num } = use(params);
  const chapterNum = parseInt(num, 10);
  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    getChapter(storyId, chapterNum)
      .then(setChapter)
      .catch((e) => setError(e.message));
  }, [storyId, chapterNum]);

  useEffect(() => {
    reload();
  }, [reload]);

  if (error) {
    return (
      <main className="max-w-3xl mx-auto p-8">
        <p className="text-red-600">加载失败：{error}</p>
        <Link href={`/stories/${storyId}`} className="text-blue-600 hover:underline">
          返回故事
        </Link>
      </main>
    );
  }

  if (!chapter) {
    return (
      <main className="max-w-3xl mx-auto p-8">
        <p className="text-gray-500">加载中...</p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <Link
          href={`/stories/${storyId}`}
          className="text-blue-600 hover:underline text-sm"
        >
          &larr; 返回故事
        </Link>
        <div className="flex gap-3 text-sm">
          {chapterNum > 1 && (
            <Link
              href={`/stories/${storyId}/chapters/${chapterNum - 1}`}
              className="text-blue-600 hover:underline"
            >
              上一章
            </Link>
          )}
          <Link
            href={`/stories/${storyId}/chapters/${chapterNum + 1}`}
            className="text-blue-600 hover:underline"
          >
            下一章
          </Link>
        </div>
      </div>
      <ChapterReader chapter={chapter} />
      <div className="mt-8">
        <ChapterVersionPanel
          storyId={storyId}
          chapterNum={chapterNum}
          onRestored={reload}
        />
      </div>
    </main>
  );
}

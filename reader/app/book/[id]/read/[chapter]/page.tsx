"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import ChapterNav from "@/components/ChapterNav";
import { readChapter } from "@/lib/api";
import type { ChapterContent } from "@/types";

export default function ReadPage({
  params,
}: {
  params: Promise<{ id: string; chapter: string }>;
}) {
  const { id: bookId, chapter } = use(params);
  const chapterNum = parseInt(chapter, 10);
  const [content, setContent] = useState<ChapterContent | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setContent(null);
    readChapter(bookId, chapterNum)
      .then(setContent)
      .catch((e) => setError(e.message));
  }, [bookId, chapterNum]);

  // Scroll to top on chapter change
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [chapterNum]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">章节未找到</p>
          <Link href={`/book/${bookId}`} className="text-amber-500 hover:underline text-sm">
            返回目录
          </Link>
        </div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
      </div>
    );
  }

  const paragraphs = content.content.split("\n").filter((p) => p.trim());

  return (
    <div className="min-h-screen">
      {/* Sticky header */}
      <header className="sticky top-0 z-10 backdrop-blur-md bg-gray-950/80 border-b border-gray-800/30">
        <div className="max-w-3xl mx-auto px-6 py-3 flex justify-between items-center">
          <Link
            href={`/book/${bookId}`}
            className="text-gray-500 hover:text-gray-300 text-sm transition"
          >
            ← {content.story_title}
          </Link>
          <span className="text-xs text-gray-600">
            第{content.chapter_num}章 · {content.word_count}字
          </span>
        </div>
      </header>

      {/* Chapter content */}
      <article className="max-w-3xl mx-auto px-6 py-10">
        {/* Chapter title */}
        <div className="text-center mb-12">
          <h1 className="text-2xl font-bold text-gray-100 tracking-wider mb-2">
            第{content.chapter_num}章
          </h1>
          {content.title && (
            <p className="text-gray-400 text-sm">{content.title}</p>
          )}
          <div className="w-12 h-px bg-amber-500/30 mx-auto mt-4" />
        </div>

        {/* Prose */}
        <div className="prose-reader">
          {paragraphs.map((p, i) =>
            p.trim() === "***" ? (
              <hr key={i} />
            ) : (
              <p key={i}>{p}</p>
            )
          )}
        </div>

        {/* Chapter navigation */}
        <ChapterNav
          bookId={bookId}
          prevChapter={content.prev_chapter}
          nextChapter={content.next_chapter}
        />
      </article>
    </div>
  );
}

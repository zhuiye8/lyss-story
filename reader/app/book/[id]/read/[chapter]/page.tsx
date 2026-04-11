"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import ReadingControls from "@/components/ReadingControls";
import ReadingSettings from "@/components/ReadingSettings";
import { ChapterSkeleton } from "@/components/SkeletonLoader";
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
  const [controlsVisible, setControlsVisible] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [fontSize, setFontSize] = useState(18);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    setContent(null);
    setError(null);
    readChapter(bookId, chapterNum)
      .then(setContent)
      .catch((e) => setError(e.message));
  }, [bookId, chapterNum]);

  useEffect(() => {
    window.scrollTo(0, 0);
    setControlsVisible(false);
  }, [chapterNum]);

  // Track scroll progress
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(docHeight > 0 ? (scrollTop / docHeight) * 100 : 0);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleContentClick = useCallback(() => {
    if (!settingsOpen) {
      setControlsVisible((v) => !v);
    }
  }, [settingsOpen]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-error mb-4">章节未找到</p>
          <Link href={`/book/${bookId}`} className="text-primary hover:underline text-sm">
            返回目录
          </Link>
        </div>
      </div>
    );
  }

  if (!content) {
    return <ChapterSkeleton />;
  }

  const paragraphs = content.content.split("\n").filter((p) => p.trim());

  return (
    <div className="min-h-screen relative" onClick={handleContentClick}>
      {/* Floating header */}
      {controlsVisible && (
        <header className="fixed top-0 left-0 right-0 z-40">
          <div className="mx-4 mt-2 px-4 py-3 bg-surface/70 backdrop-blur-xl rounded-full shadow-2xl flex items-center justify-between max-w-2xl lg:max-w-3xl lg:mx-auto">
            <Link
              href={`/book/${bookId}`}
              className="flex items-center gap-2 text-on-surface-variant hover:text-on-surface transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <span className="material-symbols-outlined text-xl">arrow_back</span>
              <span className="text-sm font-label truncate max-w-[200px]">
                {content.story_title}
              </span>
            </Link>
            <span className="text-xs font-label text-on-surface-variant/50">
              第{content.chapter_num}章 · {content.word_count}字
            </span>
          </div>
        </header>
      )}

      {/* Chapter content */}
      <article className="max-w-2xl lg:max-w-3xl mx-auto px-6 sm:px-8 py-16">
        {/* Chapter header decoration */}
        <div className="text-center mb-12">
          <div className="w-12 h-0.5 bg-primary-container mx-auto mb-6" />
          <h1 className="font-headline text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight">
            {content.title || `第${content.chapter_num}章`}
          </h1>
          <div className="flex items-center justify-center gap-3 mt-3">
            <span className="text-xs font-label text-on-surface-variant/40 tracking-widest uppercase">
              第{content.chapter_num}章
            </span>
          </div>
          <div className="flex items-center justify-center gap-2 mt-4">
            <span className="text-primary/40 text-sm">✦</span>
            <div className="w-16 h-px bg-outline-variant/20" />
            <span className="text-primary/40 text-sm">✦</span>
          </div>
        </div>

        {/* Prose */}
        <div
          className="prose-reader"
          style={{ fontSize: `${fontSize}px` }}
        >
          {paragraphs.map((p, i) =>
            p.trim() === "***" ? (
              <hr key={i} />
            ) : (
              <p key={i}>{p}</p>
            )
          )}
        </div>

        {/* End decoration */}
        <div className="text-center mt-12 mb-8">
          <div className="flex items-center justify-center gap-2">
            <div className="w-16 h-px bg-outline-variant/20" />
            <span className="text-xs font-label text-outline/40 tracking-[0.2em]">
              本章完
            </span>
            <div className="w-16 h-px bg-outline-variant/20" />
          </div>
          <p className="text-[10px] font-label text-outline/30 tracking-widest uppercase mt-3">
            本章由 狸梦小说 (Lymo Story) AI 创作
          </p>
        </div>

        {/* Inline navigation for non-floating mode */}
        <div className="flex items-center justify-between py-6 border-t border-outline-variant/10">
          {content.prev_chapter ? (
            <Link
              href={`/book/${bookId}/read/${content.prev_chapter}`}
              className="flex items-center gap-1 text-on-surface-variant hover:text-primary transition-colors font-label text-sm"
              onClick={(e) => e.stopPropagation()}
            >
              <span className="material-symbols-outlined text-lg">chevron_left</span>
              上一章
            </Link>
          ) : (
            <span className="text-xs text-on-surface-variant/30 font-label">已是第一章</span>
          )}
          <Link
            href={`/book/${bookId}`}
            className="text-on-surface-variant hover:text-primary transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            <span className="material-symbols-outlined text-xl">menu</span>
          </Link>
          {content.next_chapter ? (
            <Link
              href={`/book/${bookId}/read/${content.next_chapter}`}
              className="flex items-center gap-1 text-primary font-label text-sm font-medium"
              onClick={(e) => e.stopPropagation()}
            >
              下一章
              <span className="material-symbols-outlined text-lg">chevron_right</span>
            </Link>
          ) : (
            <span className="text-xs text-on-surface-variant/30 font-label">已是最新</span>
          )}
        </div>
      </article>

      {/* Floating controls */}
      <ReadingControls
        bookId={bookId}
        prevChapter={content.prev_chapter}
        nextChapter={content.next_chapter}
        onSettingsOpen={() => {
          setSettingsOpen(true);
          setControlsVisible(false);
        }}
        visible={controlsVisible}
      />

      {/* Reading settings drawer */}
      <ReadingSettings
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        fontSize={fontSize}
        onFontSizeChange={setFontSize}
      />

      {/* Progress bar */}
      <div className="fixed left-0 bottom-0 h-0.5 z-50 bg-gradient-to-r from-primary to-secondary transition-all duration-150"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}

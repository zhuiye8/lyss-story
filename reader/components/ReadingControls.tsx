"use client";

import Link from "next/link";

interface ReadingControlsProps {
  bookId: string;
  prevChapter: number | null;
  nextChapter: number | null;
  onSettingsOpen: () => void;
  visible: boolean;
}

export default function ReadingControls({
  bookId,
  prevChapter,
  nextChapter,
  onSettingsOpen,
  visible,
}: ReadingControlsProps) {
  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 p-4 pb-safe">
      <div className="max-w-2xl lg:max-w-3xl mx-auto flex items-center justify-between gap-3">
        {/* Prev */}
        {prevChapter ? (
          <Link
            href={`/book/${bookId}/read/${prevChapter}`}
            className="flex items-center gap-1 px-4 py-2.5 rounded-full bg-surface-container-low/80 backdrop-blur-xl text-on-surface-variant font-label text-sm hover:bg-surface-container-high transition-colors"
          >
            <span className="material-symbols-outlined text-lg">chevron_left</span>
            上一章
          </Link>
        ) : (
          <div />
        )}

        {/* Center controls */}
        <div className="flex items-center gap-4 px-5 py-2.5 bg-surface-container-low/80 backdrop-blur-xl rounded-full">
          <button
            onClick={onSettingsOpen}
            className="text-on-surface-variant hover:text-primary transition-colors"
          >
            <span className="material-symbols-outlined text-xl">format_size</span>
          </button>
          <Link
            href={`/book/${bookId}`}
            className="text-on-surface-variant hover:text-primary transition-colors"
          >
            <span className="material-symbols-outlined text-xl">menu</span>
          </Link>
        </div>

        {/* Next */}
        {nextChapter ? (
          <Link
            href={`/book/${bookId}/read/${nextChapter}`}
            className="flex items-center gap-1 px-4 py-2.5 rounded-full bg-primary-container/30 backdrop-blur-xl text-primary font-label text-sm font-medium hover:bg-primary-container/50 transition-colors"
          >
            下一章
            <span className="material-symbols-outlined text-lg">chevron_right</span>
          </Link>
        ) : (
          <span className="text-xs font-label text-on-surface-variant/40 px-4">
            已是最新
          </span>
        )}
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";

interface Props {
  bookId: string;
  prevChapter: number | null;
  nextChapter: number | null;
}

export default function ChapterNav({ bookId, prevChapter, nextChapter }: Props) {
  return (
    <div className="flex justify-between items-center py-8 border-t border-gray-800">
      {prevChapter ? (
        <Link
          href={`/book/${bookId}/read/${prevChapter}`}
          className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition text-sm"
        >
          ← 上一章
        </Link>
      ) : (
        <div />
      )}

      <Link
        href={`/book/${bookId}`}
        className="px-4 py-2 text-gray-500 hover:text-gray-300 transition text-sm"
      >
        目录
      </Link>

      {nextChapter ? (
        <Link
          href={`/book/${bookId}/read/${nextChapter}`}
          className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition text-sm"
        >
          下一章 →
        </Link>
      ) : (
        <div className="px-6 py-3 text-gray-600 text-sm">已是最新章节</div>
      )}
    </div>
  );
}

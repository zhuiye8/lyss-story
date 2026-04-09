"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { getBook } from "@/lib/api";
import type { BookDetail } from "@/types";

export default function BookDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: bookId } = use(params);
  const [book, setBook] = useState<BookDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBook(bookId)
      .then(setBook)
      .catch((e) => setError(e.message));
  }, [bookId]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">作品未找到</p>
          <Link href="/" className="text-amber-500 hover:underline text-sm">
            返回书架
          </Link>
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
      </div>
    );
  }

  const totalWords = book.chapters.reduce((sum, ch) => sum + ch.word_count, 0);

  return (
    <div className="min-h-screen">
      {/* Back */}
      <div className="max-w-3xl mx-auto px-6 pt-6">
        <Link href="/" className="text-gray-500 hover:text-gray-300 text-sm transition">
          ← 返回书架
        </Link>
      </div>

      {/* Book Info */}
      <div className="max-w-3xl mx-auto px-6 py-10">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-100 tracking-wider mb-3">
            {book.title}
          </h1>
          <div className="flex justify-center gap-3 text-sm text-gray-500 mb-4">
            <span>{book.genre}</span>
            <span>·</span>
            <span>{book.chapters.length}章</span>
            <span>·</span>
            <span>{(totalWords / 10000).toFixed(1)}万字</span>
          </div>
          <div className="w-16 h-px bg-amber-500/30 mx-auto mb-6" />
          <p className="text-gray-400 text-sm leading-relaxed max-w-xl mx-auto">
            {book.theme}
          </p>
        </div>

        {/* Characters */}
        {book.characters.length > 0 && (
          <div className="mb-10">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
              登场人物
            </h2>
            <div className="flex flex-wrap gap-2">
              {book.characters.map((c) => (
                <span
                  key={c.name}
                  className="px-3 py-1 bg-gray-800/50 rounded-full text-sm text-gray-300"
                >
                  {c.name}
                  <span className="text-gray-600 ml-1 text-xs">({c.role})</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Chapter List */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
            目录
          </h2>
          <div className="space-y-1">
            {book.chapters.map((ch) => (
              <Link
                key={ch.chapter_num}
                href={`/book/${bookId}/read/${ch.chapter_num}`}
                className="flex items-center justify-between p-4 rounded-lg hover:bg-gray-800/50 transition group"
              >
                <div>
                  <span className="text-gray-300 group-hover:text-amber-400 transition">
                    第{ch.chapter_num}章
                    {ch.title ? `　${ch.title}` : ""}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-600">
                  <span>{ch.pov}</span>
                  <span>{ch.word_count}字</span>
                </div>
              </Link>
            ))}
          </div>

          {book.chapters.length === 0 && (
            <p className="text-gray-600 text-center py-8">暂无已发布章节</p>
          )}

          {/* Start reading button */}
          {book.chapters.length > 0 && (
            <div className="text-center mt-8">
              <Link
                href={`/book/${bookId}/read/${book.chapters[0].chapter_num}`}
                className="inline-block px-8 py-3 bg-amber-600 hover:bg-amber-500 text-white rounded-lg transition font-medium"
              >
                开始阅读
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

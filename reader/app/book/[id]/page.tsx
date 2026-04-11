"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import TopBar from "@/components/TopBar";
import { DetailSkeleton } from "@/components/SkeletonLoader";
import { getBook } from "@/lib/api";
import type { BookDetail } from "@/types";

export default function BookDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: bookId } = use(params);
  const [book, setBook] = useState<BookDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getBook(bookId)
      .then(setBook)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [bookId]);

  if (loading) {
    return (
      <>
        <TopBar showBack backHref="/" title="加载中..." />
        <DetailSkeleton />
      </>
    );
  }

  if (!book) {
    return (
      <>
        <TopBar showBack backHref="/" title="未找到" />
        <div className="flex items-center justify-center h-[60vh]">
          <p className="text-on-surface-variant/60">小说不存在</p>
        </div>
      </>
    );
  }

  const totalWords = book.chapters?.reduce((sum, c) => sum + (c.word_count || 0), 0) || 0;

  return (
    <div className="min-h-screen pb-24">
      <TopBar showBack backHref="/" title={book.title} />

      <main className="max-w-3xl mx-auto px-4 sm:px-6">
        {/* Hero */}
        <section className="pt-6 pb-8">
          <div className="relative">
            <div className="absolute -top-10 right-0 w-48 h-48 bg-primary/10 rounded-full blur-[80px]" />
            <div className="relative">
              <span className="font-label text-xs uppercase tracking-[0.2em] text-primary">
                精选小说
              </span>
              <h1 className="font-headline text-3xl sm:text-4xl lg:text-5xl font-black mt-2 tracking-tight leading-tight">
                {book.title}
              </h1>
              {book.genre && (
                <div className="flex gap-2 mt-4 flex-wrap">
                  <span className="px-3 py-1 rounded-full bg-surface-container-low text-on-surface-variant font-label text-xs">
                    {book.genre}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-6 mt-6 py-4 border-y border-outline-variant/10">
            <div>
              <p className="font-headline text-xl font-bold text-primary">{book.chapters?.length || 0}</p>
              <p className="text-xs font-label text-on-surface-variant/50">章节</p>
            </div>
            <div className="w-px h-8 bg-outline-variant/20" />
            <div>
              <p className="font-headline text-xl font-bold text-primary">
                {totalWords > 10000 ? `${(totalWords / 10000).toFixed(1)}万` : totalWords}
              </p>
              <p className="text-xs font-label text-on-surface-variant/50">总字数</p>
            </div>
          </div>
        </section>

        {/* Synopsis */}
        {(book.setting || book.theme) && (
          <section className="pb-8">
            <h2 className="font-headline text-lg font-bold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-lg">auto_stories</span>
              {book.setting ? "世界观" : "简介"}
            </h2>
            <div className="font-body text-on-surface-variant/80 leading-[1.8] text-justify">
              <p className="indent-[2em]">{book.setting || book.theme}</p>
            </div>
          </section>
        )}

        {/* Characters */}
        {book.characters && book.characters.length > 0 && (
          <section className="pb-8">
            <h2 className="font-headline text-lg font-bold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-lg">group</span>
              登场人物
            </h2>
            <div className="flex gap-3 overflow-x-auto no-scrollbar pb-2">
              {book.characters.map((char, i) => (
                <div
                  key={i}
                  className="flex-shrink-0 w-32 sm:w-40 p-4 bg-surface-container-low rounded-xl"
                >
                  <div className="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center mb-3">
                    <span className="material-symbols-outlined text-primary text-lg">person</span>
                  </div>
                  <p className="font-headline text-sm font-bold truncate">{char.name}</p>
                  <p className="text-xs text-on-surface-variant/60 font-label mt-0.5 truncate">
                    {char.role}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Chapter directory */}
        {book.chapters && book.chapters.length > 0 && (
          <section className="pb-8">
            <h2 className="font-headline text-lg font-bold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-lg">list</span>
              章节目录
            </h2>
            <div className="space-y-2">
              {book.chapters.map((ch) => (
                <Link
                  key={ch.chapter_num}
                  href={`/book/${bookId}/read/${ch.chapter_num}`}
                  className="group flex items-center gap-4 p-4 bg-surface-container-low rounded-xl border-l-2 border-transparent hover:border-primary transition-all"
                >
                  <span className="font-label text-xs text-on-surface-variant/40 w-8 text-center flex-shrink-0">
                    {String(ch.chapter_num).padStart(2, "0")}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-sm font-medium group-hover:text-primary transition-colors truncate">
                      {ch.title || `第${ch.chapter_num}章`}
                    </p>
                    <div className="flex items-center gap-3 mt-1 text-xs font-label text-on-surface-variant/40">
                      {ch.word_count && <span>{ch.word_count} 字</span>}
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-on-surface-variant/20 group-hover:text-primary text-lg transition-colors">
                    chevron_right
                  </span>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Fixed CTA */}
      {book.chapters && book.chapters.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-surface/80 backdrop-blur-xl z-30">
          <div className="max-w-3xl mx-auto">
            <Link
              href={`/book/${bookId}/read/${book.chapters[0].chapter_num}`}
              className="block w-full text-center bg-primary text-on-primary font-label font-bold py-3.5 rounded-full hover:scale-[1.02] active:scale-95 transition-transform"
            >
              开始阅读
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

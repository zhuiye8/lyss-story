"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import TopBar from "@/components/TopBar";
import MascotBanner from "@/components/MascotBanner";
import { BookshelfSkeleton } from "@/components/SkeletonLoader";
import EmptyState from "@/components/EmptyState";
import { listBooks } from "@/lib/api";
import type { Book } from "@/types";

export default function DiscoverPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listBooks()
      .then(setBooks)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const featured = books[0];
  const trending = books.slice(1);
  const genres = [...new Set(books.map((b) => b.theme?.split(/[,，]/)[0]?.trim()).filter(Boolean))];

  return (
    <>
      <TopBar showLogo showSearch />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {loading ? (
          <BookshelfSkeleton />
        ) : books.length === 0 ? (
          <EmptyState
            title="梦境之扉尚未开启"
            description="这里的故事正在酝酿中，像是一场还未入眠的午后。"
            mascot="sad-pleading"
          />
        ) : (
          <div className="space-y-8">
            {/* Featured Hero */}
            {featured && (
              <section>
                <Link href={`/book/${featured.id}`} className="group block">
                  <div className="relative aspect-[16/9] sm:aspect-[21/9] rounded-xl overflow-hidden bg-surface-container-highest">
                    {/* Gradient overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/60 to-transparent z-10" />
                    {/* Decorative blur */}
                    <div className="absolute top-1/4 left-1/4 w-1/2 h-1/2 bg-primary/20 rounded-full blur-[80px]" />
                    {/* Content */}
                    <div className="absolute bottom-0 left-0 right-0 p-6 z-20">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-1 h-8 bg-primary rounded-full" />
                        <span className="font-label text-xs uppercase tracking-[0.2em] text-primary">
                          本日精选
                        </span>
                      </div>
                      <h2 className="font-headline text-2xl sm:text-3xl lg:text-4xl font-bold mb-2 group-hover:text-primary transition-colors">
                        {featured.title}
                      </h2>
                      <p className="text-on-surface-variant text-sm line-clamp-2 max-w-lg">
                        {featured.theme || "一部AI创作的精彩小说"}
                      </p>
                      <button className="mt-4 bg-primary text-on-primary font-label text-sm font-semibold px-6 py-2.5 rounded-full hover:scale-105 transition-transform">
                        入梦阅读
                      </button>
                    </div>
                  </div>
                </Link>
              </section>
            )}

            {/* Genre pills */}
            {genres.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <h3 className="font-headline text-lg font-bold">题材分类</h3>
                  <div className="h-px flex-1 bg-outline-variant/20" />
                </div>
                <div className="flex gap-3 overflow-x-auto no-scrollbar pb-2">
                  <button className="flex-shrink-0 px-4 py-2 rounded-full bg-primary text-on-primary font-label text-xs font-medium tracking-wider">
                    全部
                  </button>
                  {genres.map((genre) => (
                    <button
                      key={genre}
                      className="flex-shrink-0 px-4 py-2 rounded-full bg-surface-container-low text-on-surface-variant font-label text-xs font-medium tracking-wider hover:bg-surface-container-high transition-colors"
                    >
                      {genre}
                    </button>
                  ))}
                </div>
              </section>
            )}

            {/* Trending */}
            {trending.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <h3 className="font-headline text-lg font-bold">近期热门</h3>
                  <div className="h-px flex-1 bg-outline-variant/20" />
                </div>
                <div className="space-y-3">
                  {trending.map((book) => (
                    <Link
                      key={book.id}
                      href={`/book/${book.id}`}
                      className="group flex gap-4 p-3 rounded-xl hover:bg-surface-container-low transition-colors"
                    >
                      {/* Cover */}
                      <div className="w-20 h-28 flex-shrink-0 rounded-lg bg-surface-container-highest flex items-center justify-center border-l-2 border-primary">
                        <p className="font-headline text-xs font-bold text-on-surface text-center px-1.5 line-clamp-3">
                          {book.title}
                        </p>
                      </div>
                      {/* Info */}
                      <div className="flex-1 min-w-0 py-1">
                        <h4 className="font-headline font-bold text-on-surface group-hover:text-primary transition-colors truncate">
                          {book.title}
                        </h4>
                        <p className="text-sm text-on-surface-variant/70 mt-1 line-clamp-2">
                          {book.theme || "AI创作的小说故事"}
                        </p>
                        <div className="flex items-center gap-3 mt-2 text-xs font-label text-on-surface-variant/50">
                          <span>{book.chapter_count} 章</span>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {/* Mascot Banner */}
            <MascotBanner />
          </div>
        )}
      </main>
    </>
  );
}

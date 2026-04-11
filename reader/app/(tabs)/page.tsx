"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import BookCardBento from "@/components/BookCardBento";
import { BookshelfSkeleton } from "@/components/SkeletonLoader";
import EmptyState from "@/components/EmptyState";
import { listBooks } from "@/lib/api";
import type { Book } from "@/types";

export default function BookshelfPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listBooks()
      .then(setBooks)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <TopBar showLogo showSearch />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Section title */}
        <div className="flex items-center gap-3 mb-6">
          <h2 className="font-headline text-2xl font-bold">书架</h2>
          <div className="h-0.5 w-8 bg-primary rounded-full" />
        </div>

        {loading ? (
          <BookshelfSkeleton />
        ) : books.length === 0 ? (
          <EmptyState
            title="书架空空如也"
            description="快去发现新梦境吧"
            mascot="sad-pleading"
            actionLabel="前往发现故事"
            actionHref="/discover"
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {books.map((book) => (
              <BookCardBento key={book.id} book={book} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}

"use client";

import { useEffect, useState } from "react";
import BookCard from "@/components/BookCard";
import ThemeToggle from "@/components/ThemeToggle";
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
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-10 backdrop-blur-md bg-gray-950/80 border-b border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold tracking-wider text-gray-100">书 架</h1>
            <p className="text-xs text-gray-500 mt-0.5">AI多智能体创作</p>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Bookshelf */}
      <main className="max-w-6xl mx-auto px-6 py-10">
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="w-6 h-6 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
          </div>
        ) : books.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-500 text-lg">书架空空如也</p>
            <p className="text-gray-600 text-sm mt-2">等待作品发布中...</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {books.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-8 text-center text-xs text-gray-600">
        Powered by Story Engine — 多智能体AI小说生成系统
      </footer>
    </div>
  );
}

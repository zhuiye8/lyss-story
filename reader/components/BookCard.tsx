"use client";

import Link from "next/link";
import type { Book } from "@/types";

interface Props {
  book: Book;
}

export default function BookCard({ book }: Props) {
  return (
    <Link href={`/book/${book.id}`}>
      <div className="group relative bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
        {/* Book cover area */}
        <div className="aspect-[3/4] flex flex-col justify-between p-6">
          {/* Top decoration */}
          <div className="flex justify-between items-start">
            <div className="w-8 h-1 bg-amber-500/60 rounded" />
            <span className="text-xs text-gray-500">{book.chapter_count}章</span>
          </div>

          {/* Title */}
          <div className="flex-1 flex items-center justify-center">
            <h2 className="text-xl font-bold text-gray-100 text-center leading-relaxed tracking-wider">
              {book.title || "无题"}
            </h2>
          </div>

          {/* Bottom */}
          <div>
            <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
              {book.theme}
            </p>
            <div className="mt-3 w-full h-px bg-gradient-to-r from-transparent via-amber-500/30 to-transparent" />
          </div>
        </div>

        {/* Hover glow */}
        <div className="absolute inset-0 bg-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </div>
    </Link>
  );
}

import Link from "next/link";
import type { Book } from "@/types";

const genreColors: Record<string, string> = {
  "都市": "border-l-primary",
  "玄幻": "border-l-secondary",
  "科幻": "border-l-tertiary",
  "仙侠": "border-l-secondary",
  "悬疑": "border-l-primary",
  "历史": "border-l-tertiary",
};

export default function BookCardBento({ book }: { book: Book }) {
  const borderColor = Object.entries(genreColors).find(([key]) =>
    (book.theme || "").includes(key)
  )?.[1] || "border-l-primary";

  return (
    <Link href={`/book/${book.id}`} className="group block">
      <div className="flex gap-4 p-4 bg-surface-container-low rounded-xl glow-ember transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
        {/* Book cover */}
        <div
          className={`w-24 h-32 sm:w-28 sm:h-36 flex-shrink-0 rounded-lg bg-surface-container-highest border-l-[3px] ${borderColor} flex items-center justify-center overflow-hidden`}
        >
          <div className="text-center px-2">
            <p className="font-headline text-sm font-bold text-on-surface leading-tight line-clamp-3">
              {book.title}
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 py-1">
          <h3 className="font-headline text-base font-bold text-on-surface group-hover:text-primary transition-colors truncate">
            {book.title}
          </h3>
          {book.theme && (
            <p className="text-xs text-on-surface-variant/60 font-label mt-0.5 truncate">
              {book.theme}
            </p>
          )}
          <p className="text-sm text-on-surface-variant/80 mt-2 line-clamp-2 leading-relaxed">
            {book.theme || "AI创作的小说故事"}
          </p>
          <div className="flex items-center gap-4 mt-3 text-xs font-label text-on-surface-variant/50">
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-sm">menu_book</span>
              {book.chapter_count} 章
            </span>
            {book.updated_at && (
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-sm">schedule</span>
                {new Date(book.updated_at).toLocaleDateString("zh-CN")}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

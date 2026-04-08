"use client";

import type { ChapterDetail } from "@/types";

interface Props {
  chapter: ChapterDetail;
}

export default function ChapterReader({ chapter }: Props) {
  const paragraphs = chapter.content.split("\n").filter((p) => p.trim());

  return (
    <div className="max-w-3xl mx-auto">
      <header className="mb-8 pb-4 border-b">
        <h1 className="text-2xl font-bold mb-2">
          第{chapter.chapter_num}章
          {chapter.title ? `：${chapter.title}` : ""}
        </h1>
        <div className="flex gap-4 text-sm text-gray-500">
          <span>视角：{chapter.pov}</span>
          <span>{chapter.word_count}字</span>
        </div>
        {chapter.consistency_warnings?.length > 0 && (
          <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded text-sm">
            <p className="font-medium text-amber-700 mb-1">一致性警告：</p>
            <ul className="list-disc pl-5 text-amber-600">
              {chapter.consistency_warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </header>

      <article
        className="prose prose-lg max-w-none"
        style={{
          fontFamily: '"Noto Serif SC", "Source Han Serif SC", serif',
          lineHeight: 2,
        }}
      >
        {paragraphs.map((p, i) =>
          p.trim() === "***" ? (
            <hr key={i} className="my-8 border-gray-300" />
          ) : (
            <p key={i} className="text-justify indent-8 mb-4">
              {p}
            </p>
          )
        )}
      </article>
    </div>
  );
}

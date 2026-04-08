"use client";

import Link from "next/link";
import type { ChapterSummary } from "@/types";

interface Props {
  storyId: string;
  chapters: ChapterSummary[];
}

export default function ChapterList({ storyId, chapters }: Props) {
  if (chapters.length === 0) {
    return (
      <p className="text-gray-500 text-center py-8">
        还没有生成任何章节，点击上方按钮开始生成。
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {chapters.map((ch) => (
        <Link
          key={ch.chapter_num}
          href={`/stories/${storyId}/chapters/${ch.chapter_num}`}
          className="block p-4 border rounded-lg hover:bg-blue-50 transition"
        >
          <div className="flex justify-between items-center">
            <div>
              <span className="font-medium">
                第{ch.chapter_num}章
                {ch.title ? `：${ch.title}` : ""}
              </span>
              <span className="ml-3 text-sm text-gray-500">
                视角：{ch.pov}
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-400">
              <span>{ch.word_count}字</span>
              {ch.has_warnings && (
                <span className="text-amber-500" title="存在一致性警告">
                  !
                </span>
              )}
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}

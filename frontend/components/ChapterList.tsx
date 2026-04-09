"use client";

import Link from "next/link";
import type { ChapterSummary } from "@/types";

interface Props {
  storyId: string;
  chapters: ChapterSummary[];
  onPublishChapter?: (chapterNum: number, publish: boolean) => void;
}

export default function ChapterList({ storyId, chapters, onPublishChapter }: Props) {
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
        <div
          key={ch.chapter_num}
          className="flex items-center gap-2 p-4 border rounded-lg hover:bg-blue-50 transition"
        >
          <Link
            href={`/stories/${storyId}/chapters/${ch.chapter_num}`}
            className="flex-1"
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
          {onPublishChapter && (
            <button
              onClick={(e) => {
                e.preventDefault();
                onPublishChapter(ch.chapter_num, !ch.is_published);
              }}
              className={`px-3 py-1 text-xs rounded-full border transition ${
                ch.is_published
                  ? "bg-green-100 text-green-700 border-green-300"
                  : "bg-gray-100 text-gray-500 border-gray-300 hover:bg-green-50"
              }`}
              title={ch.is_published ? "点击取消发布" : "点击发布"}
            >
              {ch.is_published ? "已发布" : "发布"}
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

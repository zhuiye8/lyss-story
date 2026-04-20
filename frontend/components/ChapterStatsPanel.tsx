"use client";

import { useEffect, useState } from "react";
import { listChapters } from "@/lib/api";
import type { ChapterSummary } from "@/types";

interface Props {
  storyId: string;
}

export default function ChapterStatsPanel({ storyId }: Props) {
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);

  useEffect(() => {
    listChapters(storyId).then(setChapters).catch(console.error);
  }, [storyId]);

  if (chapters.length === 0) {
    return <p className="text-gray-400 text-sm text-center py-8">暂无章节数据</p>;
  }

  const totalWords = chapters.reduce((sum, c) => sum + c.word_count, 0);
  const avgWords = Math.round(totalWords / chapters.length);
  const warningCount = chapters.filter((c) => c.has_warnings).length;

  // POV distribution
  const povCounts: Record<string, number> = {};
  chapters.forEach((c) => {
    const pov = c.pov || "未知";
    povCounts[pov] = (povCounts[pov] || 0) + 1;
  });
  const povEntries = Object.entries(povCounts).sort((a, b) => b[1] - a[1]);

  const maxWordCount = Math.max(...chapters.map((c) => c.word_count), 1);

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="总章节" value={String(chapters.length)} />
        <StatCard label="总字数" value={totalWords > 10000 ? `${(totalWords / 10000).toFixed(1)}万` : String(totalWords)} />
        <StatCard label="平均字数" value={String(avgWords)} />
        <StatCard label="一致性警告" value={String(warningCount)} color={warningCount > 0 ? "text-amber-600" : undefined} />
      </div>

      {/* Word count bar chart */}
      <div>
        <h4 className="text-sm font-medium text-gray-600 mb-3">逐章字数</h4>
        <div className="space-y-1">
          {chapters.map((c) => (
            <div key={c.chapter_num} className="flex items-center gap-2 text-xs">
              <span className="w-8 text-right text-gray-400">{c.chapter_num}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                <div
                  className={`h-full rounded-full ${c.has_warnings ? "bg-amber-400" : "bg-blue-400"}`}
                  style={{ width: `${(c.word_count / maxWordCount) * 100}%` }}
                />
              </div>
              <span className="w-14 text-gray-500">{c.word_count}字</span>
            </div>
          ))}
        </div>
      </div>

      {/* POV distribution */}
      <div>
        <h4 className="text-sm font-medium text-gray-600 mb-3">视角分布</h4>
        <div className="flex gap-2 flex-wrap">
          {povEntries.map(([pov, count]) => {
            const pct = Math.round((count / chapters.length) * 100);
            return (
              <div key={pov} className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg text-sm">
                <span className="font-medium">{pov}</span>
                <span className="text-gray-400">{count}章 ({pct}%)</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg text-center">
      <p className={`text-xl font-bold ${color || "text-blue-600"}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  );
}

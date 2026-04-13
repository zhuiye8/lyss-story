"use client";

import { useState } from "react";

interface Props {
  status: string;
  onGenerateNext: (wordCount?: number) => void;
  isLoading: boolean;
}

const WORD_COUNT_OPTIONS = [1500, 2000, 2500, 3000, 4000];

export default function ControlPanel({
  status,
  onGenerateNext,
  isLoading,
}: Props) {
  const [wordCount, setWordCount] = useState(3000);
  const canGenerate = status === "bible_ready" || status === "completed" || status === "error";

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <button
        onClick={() => onGenerateNext(wordCount)}
        disabled={!canGenerate || isLoading}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
      >
        {isLoading ? "生成中..." : "生成下一章"}
      </button>
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <label htmlFor="word-count">字数</label>
        <select
          id="word-count"
          value={wordCount}
          onChange={(e) => setWordCount(Number(e.target.value))}
          disabled={isLoading}
          className="border border-gray-300 rounded px-2 py-1.5 text-sm bg-white disabled:opacity-50"
        >
          {WORD_COUNT_OPTIONS.map((n) => (
            <option key={n} value={n}>
              {n} 字
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

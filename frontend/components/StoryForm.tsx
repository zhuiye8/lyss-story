"use client";

import { useState } from "react";

interface Props {
  onSubmit: (theme: string, requirements: string, title: string) => void;
  isLoading: boolean;
}

export default function StoryForm({ onSubmit, isLoading }: Props) {
  const [title, setTitle] = useState("");
  const [theme, setTheme] = useState("");
  const [requirements, setRequirements] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (theme.trim()) onSubmit(theme.trim(), requirements.trim(), title.trim());
      }}
      className="space-y-4"
    >
      <div>
        <label className="block text-sm font-medium mb-1">
          书名（可选，留空则AI生成）
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          placeholder="例如：末世数据师、星际征途..."
          disabled={isLoading}
        />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">
          故事题材 / 主题 *
        </label>
        <textarea
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          rows={3}
          className="w-full p-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:outline-none"
          placeholder="例如：一个失忆的剑客在末世废墟中寻找自己的过去，途中遇到了一个声称认识他的神秘少女。"
          disabled={isLoading}
        />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">
          附加要求（可选）
        </label>
        <textarea
          value={requirements}
          onChange={(e) => setRequirements(e.target.value)}
          rows={2}
          className="w-full p-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:outline-none"
          placeholder="例如：玄幻风格，需要等级体系，文风偏黑暗..."
          disabled={isLoading}
        />
      </div>
      <button
        type="submit"
        disabled={isLoading || !theme.trim()}
        className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
      >
        {isLoading ? "创建中..." : "创建故事"}
      </button>
    </form>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import StoryForm from "@/components/StoryForm";
import { createStory, importOutline, listStories } from "@/lib/api";
import type { StoryResponse } from "@/types";

export default function HomePage() {
  const router = useRouter();
  const [stories, setStories] = useState<StoryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<"ai" | "import">("ai");
  const [importTitle, setImportTitle] = useState("");
  const [importText, setImportText] = useState("");

  useEffect(() => {
    listStories().then(setStories).catch(console.error);
  }, []);

  const handleSubmit = async (theme: string, requirements: string, title: string) => {
    setIsLoading(true);
    try {
      const story = await createStory(theme, requirements, title);
      router.push(`/stories/${story.story_id}`);
    } catch (e) {
      console.error(e);
      alert("创建失败，请检查后端是否启动");
    } finally {
      setIsLoading(false);
    }
  };

  const handleImport = async () => {
    if (!importText.trim()) return;
    setIsLoading(true);
    try {
      // Create a placeholder story first, then import outline
      const story = await createStory(
        importTitle || "(导入大纲)",
        "",
        importTitle
      );
      // Wait a moment for story to be created, then import
      await importOutline(story.story_id, importText.trim(), importTitle.trim());
      router.push(`/stories/${story.story_id}`);
    } catch (e) {
      console.error(e);
      alert("导入失败，请检查后端是否启动");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-2">Story Engine</h1>
      <p className="text-gray-500 mb-8">多智能体协作的AI中文长篇小说生成系统</p>

      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4">创建新故事</h2>

        {/* Mode tabs */}
        <div className="flex gap-1 mb-4 border-b">
          <button
            onClick={() => setMode("ai")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
              mode === "ai"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            AI 生成
          </button>
          <button
            onClick={() => setMode("import")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
              mode === "import"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            导入大纲
          </button>
        </div>

        {mode === "ai" ? (
          <StoryForm onSubmit={handleSubmit} isLoading={isLoading} />
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                书名（可选）
              </label>
              <input
                type="text"
                value={importTitle}
                onChange={(e) => setImportTitle(e.target.value)}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="例如：末世数据师"
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                粘贴大纲 *
              </label>
              <textarea
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                rows={12}
                className="w-full p-3 border rounded-lg resize-vertical focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono text-sm"
                placeholder={"在此粘贴你的大纲文本...\n\n支持任意格式：\n- 网文平台的大纲模板\n- 自己写的笔记\n- 世界观 + 角色 + 剧情大纲\n\nAI 会自动解析为结构化数据"}
                disabled={isLoading}
              />
              <p className="text-xs text-gray-400 mt-1">
                支持自由格式。AI 会自动提取世界观、角色、金手指、势力、分卷大纲等信息。
              </p>
            </div>
            <button
              onClick={handleImport}
              disabled={isLoading || !importText.trim()}
              className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
            >
              {isLoading ? "解析中..." : "导入并解析大纲"}
            </button>
          </div>
        )}
      </section>

      {stories.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-4">已有故事</h2>
          <div className="space-y-3">
            {stories.map((s) => (
              <button
                key={s.story_id}
                onClick={() => router.push(`/stories/${s.story_id}`)}
                className="w-full text-left p-4 border rounded-lg hover:bg-blue-50 transition"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">
                      {s.title || s.theme.slice(0, 30) + "..."}
                    </span>
                    <span className="ml-3 text-sm text-gray-400">
                      {s.chapter_count}章
                    </span>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      s.status === "bible_ready"
                        ? "bg-green-100 text-green-700"
                        : s.status === "generating"
                          ? "bg-yellow-100 text-yellow-700"
                          : s.status === "initializing"
                            ? "bg-blue-100 text-blue-700"
                            : s.status.startsWith("parsing")
                              ? "bg-purple-100 text-purple-700"
                              : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {s.status}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

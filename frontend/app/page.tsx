"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import StoryForm from "@/components/StoryForm";
import { createStory, listStories } from "@/lib/api";
import type { StoryResponse } from "@/types";

export default function HomePage() {
  const router = useRouter();
  const [stories, setStories] = useState<StoryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    listStories().then(setStories).catch(console.error);
  }, []);

  const handleSubmit = async (theme: string, requirements: string) => {
    setIsLoading(true);
    try {
      const story = await createStory(theme, requirements);
      router.push(`/stories/${story.story_id}`);
    } catch (e) {
      console.error(e);
      alert("创建失败，请检查后端是否启动");
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
        <StoryForm onSubmit={handleSubmit} isLoading={isLoading} />
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

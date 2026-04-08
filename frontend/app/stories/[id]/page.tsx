"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import StoryBibleView from "@/components/StoryBibleView";
import ChapterList from "@/components/ChapterList";
import GenerationStatus from "@/components/GenerationStatus";
import ControlPanel from "@/components/ControlPanel";
import {
  getStory,
  getStoryBible,
  listChapters,
  getStatus,
  triggerGeneration,
} from "@/lib/api";
import type { StoryResponse, StoryBible, ChapterSummary } from "@/types";

export default function StoryDashboard({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: storyId } = use(params);
  const [story, setStory] = useState<StoryResponse | null>(null);
  const [bible, setBible] = useState<StoryBible | null>(null);
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [status, setStatus] = useState<string>("loading");
  const [currentChapter, setCurrentChapter] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [s, chs, st] = await Promise.all([
        getStory(storyId),
        listChapters(storyId),
        getStatus(storyId),
      ]);
      setStory(s);
      setChapters(chs);
      setStatus(st.status);
      setCurrentChapter(st.current_chapter);
      setErrorMessage(st.error_message);

      if (s.status !== "initializing") {
        try {
          const b = await getStoryBible(storyId);
          setBible(b);
        } catch {}
      }
    } catch (e) {
      console.error(e);
    }
  }, [storyId]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 3000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await triggerGeneration(storyId);
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setIsGenerating(false), 2000);
    }
  };

  return (
    <main className="max-w-4xl mx-auto p-8">
      <Link href="/" className="text-blue-600 hover:underline text-sm mb-4 block">
        &larr; 返回首页
      </Link>

      <h1 className="text-2xl font-bold mb-2">
        {story?.title || "加载中..."}
      </h1>
      <p className="text-gray-500 mb-6 text-sm">{story?.theme}</p>

      <div className="space-y-6">
        <GenerationStatus
          status={status}
          currentChapter={currentChapter}
          errorMessage={errorMessage}
        />

        <ControlPanel
          status={status}
          onGenerateNext={handleGenerate}
          isLoading={isGenerating || status === "generating" || status === "initializing"}
        />

        {bible && <StoryBibleView bible={bible} />}

        <div>
          <h2 className="text-lg font-semibold mb-3">
            章节列表（{chapters.length}章）
          </h2>
          <ChapterList storyId={storyId} chapters={chapters} />
        </div>
      </div>
    </main>
  );
}

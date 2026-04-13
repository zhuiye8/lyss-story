"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import StoryBibleView from "@/components/StoryBibleView";
import ChapterList from "@/components/ChapterList";
import GenerationStatus from "@/components/GenerationStatus";
import ControlPanel from "@/components/ControlPanel";
import PipelineProgress from "@/components/PipelineProgress";
import {
  getStory,
  getStoryBible,
  listChapters,
  getStatus,
  getProgress,
  triggerGeneration,
  publishStory,
  publishChapter,
  type GenerationProgressData,
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
  const [progress, setProgress] = useState<GenerationProgressData | null>(null);

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

      // Fetch pipeline progress when generating
      if (st.status === "generating") {
        try {
          const p = await getProgress(storyId);
          setProgress(p);
        } catch {
          setProgress(null);
        }
      } else {
        // Keep last progress visible briefly after completion
        if (progress?.stages?.some((s) => s.status === "running")) {
          // Still has running stages, fetch one more time
          try {
            const p = await getProgress(storyId);
            setProgress(p);
          } catch {}
        }
      }

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
    // Poll faster during generation
    const interval = setInterval(refresh, status === "generating" ? 1500 : 3000);
    return () => clearInterval(interval);
  }, [refresh, status]);

  const handleGenerate = async (wordCount?: number) => {
    setIsGenerating(true);
    setProgress(null);
    try {
      await triggerGeneration(storyId, wordCount);
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

      <div className="flex items-center gap-3 mb-2">
        <h1 className="text-2xl font-bold">
          {story?.title || "加载中..."}
        </h1>
        {story && (
          <Link
            href={`/stories/${storyId}/graph`}
            className="px-3 py-1 text-xs rounded-full border border-blue-300 text-blue-600 hover:bg-blue-50 transition"
          >
            可视化
          </Link>
        )}
        {story && (
          <button
            onClick={async () => {
              await publishStory(storyId, !story.is_published);
              refresh();
            }}
            className={`px-3 py-1 text-xs rounded-full border transition ${
              story.is_published
                ? "bg-green-100 text-green-700 border-green-300"
                : "bg-gray-100 text-gray-500 border-gray-300 hover:bg-green-50"
            }`}
          >
            {story.is_published ? "已发布" : "发布小说"}
          </button>
        )}
      </div>
      <p className="text-gray-500 mb-6 text-sm">{story?.theme}</p>

      <div className="space-y-6">
        <GenerationStatus
          status={status}
          currentChapter={currentChapter}
          errorMessage={errorMessage}
        />

        {/* Pipeline progress visualization */}
        {(status === "generating" || progress?.stages?.some((s) => s.status !== "pending")) && (
          <PipelineProgress progress={progress} />
        )}

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
          <ChapterList
            storyId={storyId}
            chapters={chapters}
            onPublishChapter={async (num, pub) => {
              await publishChapter(storyId, num, pub);
              refresh();
            }}
          />
        </div>
      </div>
    </main>
  );
}

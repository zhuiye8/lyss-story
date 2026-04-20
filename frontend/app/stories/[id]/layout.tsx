"use client";

import { use, useEffect, useState } from "react";
import { DashboardSidebar } from "@/components/lymo/dashboard-sidebar";
import { getStory } from "@/lib/api";
import type { StoryResponse } from "@/types";

export default function StoryLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id: storyId } = use(params);
  const [story, setStory] = useState<StoryResponse | null>(null);

  useEffect(() => {
    let cancel = false;
    const load = async () => {
      try {
        const s = await getStory(storyId);
        if (!cancel) setStory(s);
      } catch {
        // ignore
      }
    };
    load();
    const t = setInterval(load, 5000);
    return () => {
      cancel = true;
      clearInterval(t);
    };
  }, [storyId]);

  return (
    <div className="flex min-h-[calc(100vh-56px)]">
      <DashboardSidebar
        storyId={storyId}
        storyTitle={story?.title || story?.theme}
        chapterCount={story?.chapter_count}
      />
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}

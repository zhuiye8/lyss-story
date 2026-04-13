"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import RelationshipGraph from "@/components/RelationshipGraph";
import EventTimeline from "@/components/EventTimeline";
import { getKnowledgeGraph, getEvents, listChapters } from "@/lib/api";
import type { KnowledgeGraphData, StoryEvent, ChapterSummary } from "@/types";

export default function GraphPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: storyId } = use(params);
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [events, setEvents] = useState<StoryEvent[]>([]);
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [asOfChapter, setAsOfChapter] = useState<number | undefined>(undefined);
  const [activeTab, setActiveTab] = useState<"graph" | "timeline">("graph");

  useEffect(() => {
    listChapters(storyId).then(setChapters).catch(console.error);
    getEvents(storyId).then(setEvents).catch(console.error);
  }, [storyId]);

  useEffect(() => {
    getKnowledgeGraph(storyId, asOfChapter)
      .then(setGraphData)
      .catch(console.error);
  }, [storyId, asOfChapter]);

  const maxChapter = chapters.length;

  return (
    <main className="max-w-6xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link
            href={`/stories/${storyId}`}
            className="text-blue-600 hover:underline text-sm"
          >
            &larr; 返回故事
          </Link>
          <h1 className="text-xl font-bold">可视化</h1>
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 mb-6 border-b">
        <button
          onClick={() => setActiveTab("graph")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
            activeTab === "graph"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          角色关系图谱
        </button>
        <button
          onClick={() => setActiveTab("timeline")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
            activeTab === "timeline"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          事件时间线
        </button>
      </div>

      {/* Relationship Graph */}
      {activeTab === "graph" && (
        <div>
          {/* Chapter slider */}
          {maxChapter > 0 && (
            <div className="flex items-center gap-3 mb-4">
              <label className="text-sm text-gray-600 whitespace-nowrap">
                截止章节：
              </label>
              <input
                type="range"
                min={1}
                max={maxChapter}
                value={asOfChapter ?? maxChapter}
                onChange={(e) => setAsOfChapter(Number(e.target.value))}
                className="flex-1"
              />
              <span className="text-sm font-medium w-16 text-right">
                第 {asOfChapter ?? maxChapter} 章
              </span>
              {asOfChapter && (
                <button
                  onClick={() => setAsOfChapter(undefined)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  最新
                </button>
              )}
            </div>
          )}

          {graphData ? (
            <RelationshipGraph
              nodes={graphData.nodes}
              edges={graphData.edges}
              width={900}
              height={550}
            />
          ) : (
            <p className="text-gray-500 text-sm py-8 text-center">加载中...</p>
          )}

          {/* Legend */}
          <div className="flex gap-4 mt-3 text-xs text-gray-500 justify-center">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" /> 主角
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> 对手
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-gray-500 inline-block" /> 配角
            </span>
          </div>
        </div>
      )}

      {/* Event Timeline */}
      {activeTab === "timeline" && (
        <EventTimeline events={events} />
      )}

      {/* Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4 text-center text-sm">
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">
            {graphData?.nodes.length ?? 0}
          </p>
          <p className="text-gray-500">角色</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">
            {graphData?.edges.length ?? 0}
          </p>
          <p className="text-gray-500">关系</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">{events.length}</p>
          <p className="text-gray-500">事件</p>
        </div>
      </div>
    </main>
  );
}

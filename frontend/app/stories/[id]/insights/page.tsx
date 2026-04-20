"use client";

import { use, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "motion/react";
import {
  LineChart,
  BookText,
  Clock,
  DollarSign,
  BarChart3,
  AlertTriangle,
} from "lucide-react";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { listChapters, getEvents, getStoryBible } from "@/lib/api";
import type { ChapterSummary, StoryEvent } from "@/types";
import LLMCostDashboard from "@/components/LLMCostDashboard";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });
const Chrono = dynamic(() => import("react-chrono").then((m) => m.Chrono), {
  ssr: false,
  loading: () => <Skeleton className="h-96" />,
});

export default function InsightsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: storyId } = use(params);
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [events, setEvents] = useState<StoryEvent[]>([]);
  const [bible, setBible] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [c, e, b] = await Promise.all([
          listChapters(storyId),
          getEvents(storyId).catch(() => []),
          getStoryBible(storyId).catch(() => null),
        ]);
        setChapters(c);
        setEvents(e);
        setBible(b);
      } finally {
        setLoading(false);
      }
    })();
  }, [storyId]);

  const totalWords = chapters.reduce((sum, c) => sum + (c.word_count || 0), 0);
  const avgWords = chapters.length ? Math.round(totalWords / chapters.length) : 0;
  const warnings = chapters.filter((c) => c.has_warnings).length;

  // Word count bar chart
  const wordChartOption = useMemo(() => {
    if (!chapters.length) return null;
    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "#1d252f",
        borderColor: "#2d3d4e",
        textStyle: { color: "#e8ecef" },
      },
      grid: { top: 20, left: 50, right: 20, bottom: 30 },
      xAxis: {
        type: "category",
        data: chapters.map((c) => `第${c.chapter_num}章`),
        axisLine: { lineStyle: { color: "#2d3d4e" } },
        axisLabel: {
          color: "#a8b3bd",
          fontSize: 10,
          interval: Math.max(0, Math.floor(chapters.length / 10) - 1),
        },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: "#1d252f" } },
        axisLabel: { color: "#a8b3bd", fontSize: 10 },
      },
      series: [
        {
          type: "bar",
          data: chapters.map((c) => ({
            value: c.word_count,
            itemStyle: { color: c.has_warnings ? "#c73e3a" : "#5a8fd4" },
          })),
          barWidth: "60%",
          barMaxWidth: 40,
        },
      ],
    };
  }, [chapters]);

  // POV distribution pie
  const povOption = useMemo(() => {
    const counts: Record<string, number> = {};
    chapters.forEach((c) => {
      const pov = c.pov || "未知";
      counts[pov] = (counts[pov] || 0) + 1;
    });
    const data = Object.entries(counts).map(([name, value]) => ({ name, value }));
    return {
      backgroundColor: "transparent",
      tooltip: {
        backgroundColor: "#1d252f",
        borderColor: "#2d3d4e",
        textStyle: { color: "#e8ecef" },
      },
      legend: {
        bottom: 0,
        textStyle: { color: "#a8b3bd" },
      },
      series: [
        {
          type: "pie",
          radius: ["40%", "65%"],
          center: ["50%", "45%"],
          data,
          itemStyle: {
            borderColor: "#0f1419",
            borderWidth: 2,
          },
          label: {
            color: "#e8ecef",
            fontSize: 11,
            formatter: "{b}: {c}",
          },
          color: ["#d4a84b", "#c73e3a", "#5a8fd4", "#5aa67d", "#9575cd", "#ff9472"],
        },
      ],
    };
  }, [chapters]);

  // Volume heatmap — chapters per volume with word count coloring
  const heatmapOption = useMemo(() => {
    if (!bible?.volumes?.length || !chapters.length) return null;
    const volumes = bible.volumes;
    const data: any[] = [];
    const volLabels: string[] = [];
    volumes.forEach((v: any, vi: number) => {
      const start = v.chapter_start;
      const end = v.chapter_end;
      volLabels.push(`卷${v.volume_num}`);
      for (let ch = start; ch <= end; ch++) {
        const chapter = chapters.find((c) => c.chapter_num === ch);
        const wordCount = chapter?.word_count || 0;
        data.push([ch - start, vi, wordCount]);
      }
    });
    const maxChapters = Math.max(...volumes.map((v: any) => (v.chapter_end || 0) - (v.chapter_start || 0) + 1));
    return {
      backgroundColor: "transparent",
      tooltip: {
        position: "top",
        backgroundColor: "#1d252f",
        borderColor: "#2d3d4e",
        textStyle: { color: "#e8ecef" },
        formatter: (p: any) => {
          const [x, y, v] = p.data;
          const vol = volumes[y];
          const chNum = (vol.chapter_start || 1) + x;
          return `第${chNum}章<br/>字数：${v || "未生成"}`;
        },
      },
      grid: { top: 30, left: 50, right: 30, bottom: 30 },
      xAxis: {
        type: "category",
        data: Array.from({ length: maxChapters }, (_, i) => i + 1),
        axisLine: { lineStyle: { color: "#2d3d4e" } },
        axisLabel: { color: "#a8b3bd", fontSize: 10 },
        splitArea: { show: false },
      },
      yAxis: {
        type: "category",
        data: volLabels,
        axisLine: { lineStyle: { color: "#2d3d4e" } },
        axisLabel: { color: "#a8b3bd", fontSize: 10 },
        splitArea: { show: false },
      },
      visualMap: {
        min: 0,
        max: 5000,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: "0%",
        textStyle: { color: "#a8b3bd" },
        inRange: {
          color: ["#151b23", "#4374b5", "#5a8fd4", "#d4a84b", "#c73e3a"],
        },
      },
      series: [
        {
          type: "heatmap",
          data,
          label: { show: false },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowColor: "rgba(212,168,75,0.5)" },
          },
        },
      ],
    };
  }, [bible, chapters]);

  // Timeline events for react-chrono
  const timelineItems = useMemo(() => {
    return events.slice(0, 100).map((e: any) => ({
      title: `T${e.time}`,
      cardTitle: e.description?.slice(0, 50) || "未命名事件",
      cardDetailedText: [
        e.description,
        e.location ? `📍 ${e.location}` : "",
        e.effects?.length ? `📌 ${e.effects.slice(0, 2).join("；")}` : "",
      ]
        .filter(Boolean)
        .join("\n"),
    }));
  }, [events]);

  return (
    <div className="px-8 py-6 max-w-7xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-serif text-3xl font-bold flex items-center gap-3 mb-2">
          <LineChart className="size-7 text-lymo-gold-400" />
          数据洞察
        </h1>
        <p className="text-sm text-muted-foreground">
          {chapters.length} 章 · {totalWords.toLocaleString()} 字 · 平均 {avgWords} 字/章
        </p>
      </motion.div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="章节总数" value={chapters.length} icon={<BookText className="size-4" />} />
        <StatCard
          label="总字数"
          value={totalWords.toLocaleString()}
          icon={<BookText className="size-4" />}
          accent="gold"
        />
        <StatCard
          label="平均字数/章"
          value={avgWords}
          icon={<BarChart3 className="size-4" />}
          accent="stellar"
        />
        <StatCard
          label="一致性警告"
          value={warnings}
          icon={<AlertTriangle className="size-4" />}
          accent={warnings > 0 ? "warn" : "jade"}
        />
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">
            <BarChart3 className="size-3.5 mr-1.5" />
            概览
          </TabsTrigger>
          <TabsTrigger value="heatmap">
            <BookText className="size-3.5 mr-1.5" />
            章节热力图
          </TabsTrigger>
          <TabsTrigger value="timeline">
            <Clock className="size-3.5 mr-1.5" />
            事件时间线
          </TabsTrigger>
          <TabsTrigger value="cost">
            <DollarSign className="size-3.5 mr-1.5" />
            LLM 成本
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {loading ? (
            <Skeleton className="h-96" />
          ) : (
            <div className="grid lg:grid-cols-3 gap-6">
              <Card className="p-5 lg:col-span-2">
                <h3 className="font-serif font-semibold mb-3">每章字数</h3>
                <div className="h-72">
                  {wordChartOption && (
                    <ReactECharts option={wordChartOption} style={{ height: "100%", width: "100%" }} />
                  )}
                </div>
              </Card>
              <Card className="p-5">
                <h3 className="font-serif font-semibold mb-3">视角分布</h3>
                <div className="h-72">
                  <ReactECharts option={povOption} style={{ height: "100%", width: "100%" }} />
                </div>
              </Card>
            </div>
          )}

          {/* Chapters list with scores */}
          <Card className="p-5">
            <h3 className="font-serif font-semibold mb-4">章节列表</h3>
            <div className="space-y-1.5 max-h-[400px] overflow-y-auto">
              {chapters.map((c) => (
                <Link
                  key={c.chapter_num}
                  href={`/stories/${storyId}/chapters/${c.chapter_num}`}
                  className="flex items-center gap-3 p-2.5 rounded-md hover:bg-secondary/50 transition group"
                >
                  <Badge variant="outline" className="w-12 justify-center font-mono text-[10px]">
                    {c.chapter_num.toString().padStart(2, "0")}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-serif font-medium truncate">
                      {c.title || `第 ${c.chapter_num} 章`}
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-2">
                      <span>{c.word_count} 字</span>
                      <span>·</span>
                      <span className="truncate">{c.pov || "未指定"}</span>
                    </div>
                  </div>
                  {c.has_warnings && <Badge variant="destructive" className="text-[9px]">警告</Badge>}
                  {c.is_published && <Badge variant="jade" className="text-[9px]">已发布</Badge>}
                </Link>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="heatmap">
          <Card className="p-5">
            <h3 className="font-serif font-semibold mb-3">章节热力图（按卷）</h3>
            <p className="text-xs text-muted-foreground mb-4">
              颜色深浅表示该章字数 · 深色代表未生成
            </p>
            <div className="h-[500px]">
              {heatmapOption ? (
                <ReactECharts option={heatmapOption} style={{ height: "100%", width: "100%" }} />
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                  暂无分卷大纲数据
                </div>
              )}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="timeline">
          <Card className="p-5">
            <h3 className="font-serif font-semibold mb-3">
              事件时间线（{events.length} 个事件）
            </h3>
            <div className="h-[600px]">
              {timelineItems.length === 0 ? (
                <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                  暂无事件数据
                </div>
              ) : (
                <Chrono
                  items={timelineItems}
                  mode="VERTICAL_ALTERNATING"
                  theme={{
                    primary: "#d4a84b",
                    secondary: "#c73e3a",
                    cardBgColor: "#1d252f",
                    titleColor: "#d4a84b",
                    titleColorActive: "#e0bc6a",
                  }}
                  fontSizes={{
                    cardSubtitle: "0.75rem",
                    cardText: "0.75rem",
                    cardTitle: "0.95rem",
                    title: "0.85rem",
                  }}
                  cardHeight={100}
                  disableToolbar
                />
              )}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="cost">
          <LLMCostDashboard />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  accent = "default",
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  accent?: "default" | "gold" | "stellar" | "jade" | "warn";
}) {
  const color =
    accent === "gold"
      ? "text-lymo-gold-400"
      : accent === "stellar"
      ? "text-lymo-stellar-400"
      : accent === "jade"
      ? "text-lymo-jade-400"
      : accent === "warn"
      ? "text-lymo-vermilion-400"
      : "text-muted-foreground";
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className={color}>{icon}</span>
      </div>
      <div className="font-serif text-2xl font-bold tabular-nums">{value}</div>
    </Card>
  );
}

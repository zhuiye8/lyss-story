"use client";

import { use, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "motion/react";
import { ArrowLeft, Quote, Shield, Zap, Users } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { CharacterAvatar } from "@/components/lymo/character-avatar";
import { getCharacters, getKnowledgeGraph, getStoryBible, getCharacterArcHistory } from "@/lib/api";
import type { CharacterWithArc, KnowledgeGraphData } from "@/types";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export default function CharacterDetailPage({
  params,
}: {
  params: Promise<{ id: string; cid: string }>;
}) {
  const { id: storyId, cid: rawCid } = use(params);
  const cid = decodeURIComponent(rawCid);
  const [char, setChar] = useState<any | null>(null);
  const [kg, setKG] = useState<KnowledgeGraphData | null>(null);
  const [arcHistory, setArcHistory] = useState<any>(null);
  const [allChars, setAllChars] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [bible, kgData, arcH, chars] = await Promise.all([
          getStoryBible(storyId),
          getKnowledgeGraph(storyId),
          getCharacterArcHistory(storyId, cid).catch(() => ({ arcs: [], states: [] })),
          getCharacters(storyId),
        ]);
        const flat = [
          bible.protagonist,
          bible.antagonist,
          ...(bible.supporting_characters || []),
        ].filter(Boolean) as any[];
        const found = flat.find((c: any) => c.character_id === cid);
        setChar(found);
        setKG(kgData);
        setArcHistory(arcH);
        setAllChars(flat);
      } finally {
        setLoading(false);
      }
    })();
  }, [storyId, cid]);

  const relationships = useMemo(() => {
    if (!kg) return [];
    const idToName = new Map(allChars.map((c: any) => [c.character_id, c.name]));
    return kg.edges
      .filter((e: any) => e.source === cid || e.target === cid)
      .map((e: any) => {
        const isSubject = e.source === cid;
        const otherId = isSubject ? e.target : e.source;
        return {
          direction: isSubject ? "out" : "in",
          predicate: e.predicate,
          otherId,
          otherName: idToName.get(otherId) || otherId,
          detail: e.detail || "",
          chapter: e.valid_from,
        };
      });
  }, [kg, cid, allChars]);

  // Arc emotion timeline for ECharts
  const emotionOption = useMemo(() => {
    if (!arcHistory?.states?.length) return null;
    const states = [...arcHistory.states].sort((a: any, b: any) => a.chapter_num - b.chapter_num);
    // Simple sentiment heuristic
    const score = (s: string = "") => {
      if (/喜|悦|爱|安|信任|激动/.test(s)) return 1;
      if (/悲|怒|怕|痛|恨|绝望|麻木/.test(s)) return -1;
      if (/疑|虑|惑|犹|紧张|复杂/.test(s)) return -0.3;
      return 0;
    };
    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "#1d252f",
        borderColor: "#2d3d4e",
        textStyle: { color: "#e8ecef" },
        formatter: (params: any) => {
          const p = params[0];
          const state = states[p.dataIndex];
          return `第${state.chapter_num}章<br/>情绪：${state.emotional_state || "无"}<br/>目标：${state.goals_update || "无"}`;
        },
      },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: {
        type: "category",
        data: states.map((s: any) => `第${s.chapter_num}章`),
        axisLine: { lineStyle: { color: "#2d3d4e" } },
        axisLabel: { color: "#a8b3bd", fontSize: 10 },
      },
      yAxis: {
        type: "value",
        min: -1,
        max: 1,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: "#1d252f" } },
        axisLabel: {
          color: "#a8b3bd",
          fontSize: 10,
          formatter: (v: number) => (v > 0.5 ? "积极" : v < -0.5 ? "消极" : v === 0 ? "平" : ""),
        },
      },
      series: [
        {
          type: "line",
          smooth: true,
          symbolSize: 8,
          data: states.map((s: any) => score(s.emotional_state || "")),
          lineStyle: { width: 3, color: "#d4a84b" },
          itemStyle: { color: "#d4a84b", borderColor: "#d4a84b" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(212,168,75,0.3)" },
                { offset: 1, color: "rgba(212,168,75,0)" },
              ],
            },
          },
        },
      ],
    };
  }, [arcHistory]);

  if (loading || !char) {
    return (
      <div className="px-8 py-6 max-w-5xl mx-auto space-y-4">
        <Skeleton className="h-10 w-1/2" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton className="h-64" />
          <Skeleton className="h-64 col-span-2" />
        </div>
      </div>
    );
  }

  return (
    <div className="px-8 py-6 max-w-6xl mx-auto space-y-6">
      <Link href={`/stories/${storyId}/characters`}>
        <Button variant="ghost" size="sm" className="-ml-2">
          <ArrowLeft className="size-3.5" />
          返回角色画廊
        </Button>
      </Link>

      {/* Hero card */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="p-8 relative overflow-hidden">
          <div
            className="absolute -top-32 -right-32 w-80 h-80 rounded-full opacity-20 blur-3xl"
            style={{
              background:
                char.role === "protagonist"
                  ? "#d4a84b"
                  : char.role === "antagonist"
                  ? "#c73e3a"
                  : "#5a8fd4",
            }}
          />
          <div className="relative flex flex-col md:flex-row gap-6 items-start">
            <CharacterAvatar name={char.name} role={char.role} size="xl" />
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-3 mb-2">
                <h1 className="font-serif text-4xl font-bold">{char.name}</h1>
                <Badge
                  variant={
                    char.role === "protagonist"
                      ? "gold"
                      : char.role === "antagonist"
                      ? "vermilion"
                      : "stellar"
                  }
                >
                  {char.role === "protagonist"
                    ? "主角"
                    : char.role === "antagonist"
                    ? "反派"
                    : "配角"}
                </Badge>
              </div>
              <div className="flex flex-wrap gap-3 text-sm text-muted-foreground mb-4">
                {char.gender && <span>{char.gender}</span>}
                {char.age && <span>{char.age}</span>}
                {char.appearance && <span className="italic">· {char.appearance}</span>}
              </div>
              {char.personality && (
                <p className="font-serif italic text-lg leading-relaxed text-muted-foreground border-l-2 border-lymo-gold-500/40 pl-4">
                  "{char.personality}"
                </p>
              )}
            </div>
          </div>
        </Card>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: background + goals + weaknesses */}
        <div className="space-y-6">
          {char.background && (
            <Card className="p-5">
              <h3 className="font-serif font-bold mb-3 flex items-center gap-2">
                <span className="text-lymo-gold-400">人物背景</span>
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {char.background}
              </p>
            </Card>
          )}

          {(char.goals?.length > 0 || char.weaknesses?.length > 0) && (
            <Card className="p-5">
              {char.goals?.length > 0 && (
                <div className="mb-5">
                  <h3 className="font-serif font-bold text-sm text-lymo-jade-400 mb-2 flex items-center gap-1.5">
                    <Zap className="size-4" /> 目标
                  </h3>
                  <ul className="space-y-1.5 text-sm">
                    {char.goals.map((g: string, i: number) => (
                      <li key={i} className="pl-4 relative text-muted-foreground">
                        <span className="absolute left-0 text-lymo-jade-400">·</span>
                        {g}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {char.weaknesses?.length > 0 && (
                <div>
                  <h3 className="font-serif font-bold text-sm text-lymo-vermilion-300 mb-2 flex items-center gap-1.5">
                    <Shield className="size-4" /> 弱点
                  </h3>
                  <ul className="space-y-1.5 text-sm">
                    {char.weaknesses.map((w: string, i: number) => (
                      <li key={i} className="pl-4 relative text-muted-foreground">
                        <span className="absolute left-0 text-lymo-vermilion-400">·</span>
                        {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          )}
        </div>

        {/* Middle + Right: Speech, Hard constraints, Emotion timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* Speech examples */}
          {(char.speech_examples?.length > 0 || char.speech_rules?.length > 0) && (
            <Card className="p-5">
              <h3 className="font-serif font-bold mb-4 flex items-center gap-2">
                <Quote className="size-4 text-lymo-gold-400" />
                <span>说话风格</span>
              </h3>
              {char.speech_examples?.length > 0 && (
                <div className="space-y-2 mb-4">
                  {char.speech_examples.map((s: string, i: number) => (
                    <div
                      key={i}
                      className="font-serif text-sm italic p-3 rounded-md bg-secondary/30 border-l-2 border-lymo-gold-500/60"
                    >
                      「{s}」
                    </div>
                  ))}
                </div>
              )}
              {char.speech_rules?.length > 0 && (
                <div className="pt-3 border-t border-border/40">
                  <div className="text-[10px] tracking-wider font-semibold text-muted-foreground uppercase mb-2">
                    硬规则
                  </div>
                  <ul className="space-y-1">
                    {char.speech_rules.map((r: string, i: number) => (
                      <li key={i} className="text-xs text-muted-foreground flex gap-2">
                        <span className="text-lymo-gold-400">·</span>
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          )}

          {/* Hard constraints */}
          {char.hard_constraints?.length > 0 && (
            <Card className="p-5 border-lymo-vermilion-500/30">
              <h3 className="font-serif font-bold mb-3 flex items-center gap-2">
                <Shield className="size-4 text-lymo-vermilion-400" />
                <span>不可违反的底线</span>
              </h3>
              <ul className="space-y-2">
                {char.hard_constraints.map((c: string, i: number) => (
                  <li
                    key={i}
                    className="text-sm flex gap-2 p-2 rounded bg-lymo-vermilion-500/5 border-l-2 border-lymo-vermilion-500/60"
                  >
                    <span className="text-lymo-vermilion-400 shrink-0">⚠</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Emotion timeline */}
          {emotionOption && (
            <Card className="p-5">
              <h3 className="font-serif font-bold mb-4">情绪轨迹</h3>
              <div className="h-48">
                <ReactECharts option={emotionOption} style={{ height: "100%", width: "100%" }} />
              </div>
            </Card>
          )}

          {/* Relationships */}
          {relationships.length > 0 && (
            <Card className="p-5">
              <h3 className="font-serif font-bold mb-4 flex items-center gap-2">
                <Users className="size-4 text-lymo-stellar-400" />
                <span>关系网 ({relationships.length})</span>
              </h3>
              <div className="grid md:grid-cols-2 gap-2">
                {relationships.slice(0, 12).map((r: any, i: number) => (
                  <Link
                    key={i}
                    href={`/stories/${storyId}/characters/${encodeURIComponent(r.otherId)}`}
                    className="flex items-center gap-3 p-2 rounded-md hover:bg-secondary/40 transition"
                  >
                    <CharacterAvatar
                      name={r.otherName}
                      role={allChars.find((c: any) => c.character_id === r.otherId)?.role}
                      size="sm"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{r.otherName}</div>
                      <div className="text-[11px] text-muted-foreground">
                        {r.direction === "out" ? "→" : "←"} {r.predicate}
                        {r.chapter && (
                          <span className="ml-1 text-[9px] text-muted-foreground/60">ch{r.chapter}</span>
                        )}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </Card>
          )}

          {/* Arc history */}
          {arcHistory?.arcs?.length > 0 && (
            <Card className="p-5">
              <h3 className="font-serif font-bold mb-4">弧线演进</h3>
              <div className="space-y-3">
                {arcHistory.arcs.map((a: any, i: number) => {
                  const summary = a.summary || {};
                  return (
                    <div
                      key={i}
                      className="p-3 border border-border/40 rounded-md bg-secondary/20"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-serif font-bold text-sm">
                          {a.arc_name || "未命名弧线"}
                        </span>
                        <Badge variant="ghost" className="text-[9px]">
                          ch{a.chapter_num}
                        </Badge>
                      </div>
                      {summary.current_phase && (
                        <div className="text-xs text-lymo-gold-400 mb-1">
                          阶段：{summary.current_phase}
                        </div>
                      )}
                      {summary.emotional_trajectory && (
                        <p className="text-xs text-muted-foreground">
                          {summary.emotional_trajectory}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

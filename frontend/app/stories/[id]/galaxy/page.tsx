"use client";

import { use, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { motion } from "motion/react";
import { Orbit, ArrowRight, Sparkles, Info, Maximize2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { CharacterAvatar } from "@/components/lymo/character-avatar";
import { getCharacters, getKnowledgeGraph, getStoryBible } from "@/lib/api";
import type { CharacterWithArc, KnowledgeGraphData } from "@/types";

const Galaxy3D = dynamic(
  () => import("@/components/lymo/galaxy-3d").then((m) => m.Galaxy3D),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center bg-lymo-ink-950">
        <div className="text-center">
          <Skeleton className="h-8 w-48 mb-3 mx-auto" />
          <div className="text-sm text-muted-foreground font-serif">
            正在点燃星辰...
          </div>
        </div>
      </div>
    ),
  }
);

export default function GalaxyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: storyId } = use(params);
  const [chars, setChars] = useState<CharacterWithArc[]>([]);
  const [bibleChars, setBibleChars] = useState<any[]>([]);
  const [kg, setKG] = useState<KnowledgeGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any | null>(null);
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [c, k, b] = await Promise.all([
          getCharacters(storyId),
          getKnowledgeGraph(storyId),
          getStoryBible(storyId).catch(() => null),
        ]);
        setChars(c);
        setKG(k);
        if (b) {
          const flat = [
            b.protagonist,
            b.antagonist,
            ...(b.supporting_characters || []),
          ].filter(Boolean);
          setBibleChars(flat);
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [storyId]);

  const roleCount = {
    protagonist: chars.filter((c: any) => c.role === "protagonist").length,
    antagonist: chars.filter((c: any) => c.role === "antagonist").length,
    supporting: chars.filter((c: any) => c.role === "supporting").length,
  };

  return (
    <div className="relative">
      {/* Header — compact */}
      <div className={fullscreen ? "hidden" : "px-8 py-6 max-w-7xl mx-auto"}>
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-end justify-between mb-4"
        >
          <div>
            <h1 className="font-serif text-3xl font-bold flex items-center gap-3">
              <Orbit className="size-7 text-lymo-gold-400" />
              <span className="text-gold-grad">角色宇宙</span>
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              3D 交互式关系图谱 · 拖动旋转 · 滚轮缩放 · 点击聚焦
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-3 text-[11px] text-muted-foreground mr-3">
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-lymo-gold-400 glow-gold" />
                主角 {roleCount.protagonist}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-lymo-vermilion-400" />
                反派 {roleCount.antagonist}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-lymo-stellar-400" />
                配角 {roleCount.supporting}
              </span>
            </div>
            <Button
              size="sm"
              variant="gold"
              onClick={() => setFullscreen(true)}
              disabled={loading}
            >
              <Maximize2 className="size-3.5" />
              全屏沉浸
            </Button>
          </div>
        </motion.div>
      </div>

      {/* Galaxy canvas */}
      <div
        className={
          fullscreen
            ? "fixed inset-0 z-50 bg-lymo-ink-950"
            : "px-8 max-w-7xl mx-auto"
        }
      >
        <Card
          className={
            fullscreen
              ? "h-screen w-screen rounded-none border-0 overflow-hidden"
              : "h-[700px] overflow-hidden relative"
          }
        >
          {fullscreen && (
            <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setFullscreen(false)}
                className="bg-card/80 backdrop-blur"
              >
                退出全屏
              </Button>
            </div>
          )}

          {loading ? (
            <div className="w-full h-full flex items-center justify-center">
              <div className="text-center">
                <div className="mb-4 text-lymo-gold-400 font-serif text-lg">
                  <Sparkles className="size-6 inline mr-2 animate-pulse" />
                  正在点燃星辰...
                </div>
                <div className="flex gap-1 justify-center">
                  <div className="w-2 h-2 rounded-full bg-lymo-gold-500 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 rounded-full bg-lymo-gold-500 animate-bounce" style={{ animationDelay: "200ms" }} />
                  <div className="w-2 h-2 rounded-full bg-lymo-gold-500 animate-bounce" style={{ animationDelay: "400ms" }} />
                </div>
              </div>
            </div>
          ) : !kg || chars.length === 0 ? (
            <div className="w-full h-full flex items-center justify-center">
              <div className="text-center">
                <Orbit className="size-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                <p className="text-sm text-muted-foreground">
                  暂无角色数据，请先生成故事设定
                </p>
              </div>
            </div>
          ) : (
            <Galaxy3D
              characters={chars}
              kg={kg}
              bibleChars={bibleChars}
              onSelectCharacter={setSelected}
            />
          )}
        </Card>

        {/* Helper strip (only visible when not fullscreen) */}
        {!fullscreen && (
          <div className="mt-4 flex items-center gap-2 text-[11px] text-muted-foreground">
            <Info className="size-3" />
            <span>绿色连线表示正向关系（信任/爱），红色表示敌对/伤害，金色表示血缘/师徒</span>
          </div>
        )}
      </div>

      {/* Character detail sheet */}
      <Sheet open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <SheetContent side="right" className="w-[500px] sm:max-w-[500px]">
          {selected && (
            <>
              <SheetHeader>
                <div className="flex items-center gap-4 mb-2">
                  <CharacterAvatar
                    name={selected.name}
                    role={selected.role}
                    size="xl"
                  />
                  <div>
                    <SheetTitle className="font-serif text-2xl mb-1">
                      {selected.name}
                    </SheetTitle>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          selected.role === "protagonist"
                            ? "gold"
                            : selected.role === "antagonist"
                            ? "vermilion"
                            : "stellar"
                        }
                      >
                        {selected.role === "protagonist"
                          ? "主角"
                          : selected.role === "antagonist"
                          ? "反派"
                          : "配角"}
                      </Badge>
                      {selected.gender && (
                        <span className="text-xs text-muted-foreground">
                          {selected.gender}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <SheetDescription>
                  {selected.personality || "——"}
                </SheetDescription>
              </SheetHeader>

              <div className="mt-5 space-y-4">
                {selected.background && (
                  <div>
                    <div className="text-[10px] tracking-wider uppercase font-semibold text-muted-foreground mb-1">
                      背景
                    </div>
                    <p className="text-sm leading-relaxed">{selected.background}</p>
                  </div>
                )}

                {selected.goals?.length > 0 && (
                  <div>
                    <div className="text-[10px] tracking-wider uppercase font-semibold text-lymo-jade-400 mb-2">
                      目标
                    </div>
                    <ul className="space-y-1">
                      {selected.goals.map((g: string, i: number) => (
                        <li key={i} className="text-sm flex gap-2">
                          <span className="text-lymo-jade-400">·</span> {g}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {selected.weaknesses?.length > 0 && (
                  <div>
                    <div className="text-[10px] tracking-wider uppercase font-semibold text-lymo-vermilion-400 mb-2">
                      弱点
                    </div>
                    <ul className="space-y-1">
                      {selected.weaknesses.map((w: string, i: number) => (
                        <li key={i} className="text-sm flex gap-2">
                          <span className="text-lymo-vermilion-400">·</span> {w}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Link
                  href={`/stories/${storyId}/characters/${encodeURIComponent(selected.id)}`}
                  className="flex items-center justify-between p-3 rounded-md bg-lymo-gold-500/10 border border-lymo-gold-500/30 hover:bg-lymo-gold-500/20 transition group"
                >
                  <span className="text-sm font-serif font-medium text-lymo-gold-400">
                    查看角色详情页
                  </span>
                  <ArrowRight className="size-4 text-lymo-gold-400 group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

"use client";

import { use, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "motion/react";
import { Users, Orbit, Network, ArrowRight } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CharacterAvatar } from "@/components/lymo/character-avatar";
import { getCharacters, getKnowledgeGraph, getStoryBible } from "@/lib/api";
import type { CharacterWithArc, KnowledgeGraphData } from "@/types";

// reagraph must be SSR-disabled
const GraphCanvas = dynamic(
  () => import("reagraph").then((m) => m.GraphCanvas),
  { ssr: false, loading: () => <Skeleton className="w-full h-[500px]" /> }
);

const ROLE_COLORS: Record<string, string> = {
  protagonist: "#d4a84b", // gold
  antagonist: "#c73e3a", // vermilion
  supporting: "#5a8fd4", // stellar
};

export default function CharactersGalleryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: storyId } = use(params);
  const [chars, setChars] = useState<CharacterWithArc[]>([]);
  const [kg, setKG] = useState<KnowledgeGraphData | null>(null);
  const [bible, setBible] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

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
        setBible(b);
      } finally {
        setLoading(false);
      }
    })();
  }, [storyId]);

  // Enrich characters with bible data
  const enriched = useMemo(() => {
    if (!bible) return chars as any[];
    const flat = [
      bible.protagonist,
      bible.antagonist,
      ...(bible.supporting_characters || []),
    ].filter(Boolean);
    const byId = new Map(flat.map((c: any) => [c.character_id, c]));
    return chars.map((c: any) => ({ ...byId.get(c.character_id), ...c }));
  }, [chars, bible]);

  const graphNodes = useMemo(
    () =>
      enriched.map((c: any) => ({
        id: c.character_id,
        label: c.name,
        fill: ROLE_COLORS[c.role] || "#6b7785",
        size: c.role === "protagonist" ? 16 : c.role === "antagonist" ? 14 : 10,
        data: c,
      })),
    [enriched]
  );

  const graphEdges = useMemo(() => {
    if (!kg) return [];
    const validIds = new Set(enriched.map((c: any) => c.character_id));
    const edges: any[] = [];
    kg.edges.forEach((e: any, i: number) => {
      if (validIds.has(e.source) && validIds.has(e.target)) {
        edges.push({
          id: `e-${i}`,
          source: e.source,
          target: e.target,
          label: e.predicate || "",
        });
      }
    });
    return edges;
  }, [kg, enriched]);

  return (
    <div className="px-8 py-6 max-w-7xl mx-auto space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-end justify-between mb-2"
      >
        <div>
          <h1 className="font-serif text-3xl font-bold flex items-center gap-3">
            <Users className="size-7 text-lymo-gold-400" />
            角色画廊
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {loading ? "加载中..." : `共 ${enriched.length} 位角色 · ${graphEdges.length} 条关系`}
          </p>
        </div>
        <Link href={`/stories/${storyId}/galaxy`}>
          <Button variant="gold" size="sm">
            <Orbit className="size-4" />
            进入 3D 宇宙
          </Button>
        </Link>
      </motion.div>

      {/* Relationship graph */}
      <Card className="p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network className="size-4 text-lymo-stellar-400" />
            <span className="font-serif font-semibold">角色关系图谱</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="size-2 rounded-full" style={{ background: ROLE_COLORS.protagonist }} />
              主角
            </span>
            <span className="flex items-center gap-1">
              <span className="size-2 rounded-full" style={{ background: ROLE_COLORS.antagonist }} />
              反派
            </span>
            <span className="flex items-center gap-1">
              <span className="size-2 rounded-full" style={{ background: ROLE_COLORS.supporting }} />
              配角
            </span>
          </div>
        </div>
        <div className="h-[500px] bg-lymo-ink-950 relative">
          {loading ? (
            <Skeleton className="w-full h-full" />
          ) : graphNodes.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm">
              暂无角色数据
            </div>
          ) : (
            <GraphCanvas
              nodes={graphNodes}
              edges={graphEdges}
              labelType="all"
              edgeArrowPosition="end"
              edgeLabelPosition="natural"
              layoutType="forceDirected2d"
              cameraMode="pan"
              theme={{
                canvas: { background: "#0b0f14" },
                node: {
                  fill: "#2d3d4e",
                  activeFill: "#d4a84b",
                  opacity: 1,
                  selectedOpacity: 1,
                  inactiveOpacity: 0.2,
                  label: {
                    color: "#e8ecef",
                    activeColor: "#d4a84b",
                    stroke: "#0b0f14",
                  },
                },
                edge: {
                  fill: "#2d3d4e",
                  activeFill: "#c73e3a",
                  opacity: 0.5,
                  selectedOpacity: 1,
                  inactiveOpacity: 0.1,
                  label: {
                    stroke: "#0b0f14",
                    color: "#a8b3bd",
                    activeColor: "#d4a84b",
                  },
                },
                arrow: { fill: "#2d3d4e", activeFill: "#c73e3a" },
                lasso: { border: "#d4a84b", background: "rgba(212,168,75,0.1)" },
                ring: { fill: "#2d3d4e", activeFill: "#d4a84b" },
                cluster: {
                  stroke: "#2d3d4e",
                  label: { color: "#a8b3bd", stroke: "#0b0f14" },
                },
              }}
            />
          )}
        </div>
      </Card>

      {/* Character cards grid */}
      <div>
        <h2 className="font-serif text-xl font-bold mb-4">全部角色</h2>
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        ) : (
          <motion.div
            initial="hidden"
            animate="show"
            variants={{
              hidden: {},
              show: { transition: { staggerChildren: 0.05 } },
            }}
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {enriched.map((c: any) => (
              <motion.div
                key={c.character_id}
                variants={{
                  hidden: { opacity: 0, y: 10 },
                  show: { opacity: 1, y: 0 },
                }}
              >
                <Link href={`/stories/${storyId}/characters/${encodeURIComponent(c.character_id)}`}>
                  <Card className="p-5 card-hover cursor-pointer group relative overflow-hidden h-full">
                    <div
                      className="absolute -top-16 -right-16 w-32 h-32 rounded-full opacity-20 group-hover:opacity-30 transition-opacity blur-2xl"
                      style={{ background: ROLE_COLORS[c.role] || "#6b7785" }}
                    />
                    <div className="relative">
                      <div className="flex items-start gap-4 mb-4">
                        <CharacterAvatar name={c.name} role={c.role} size="lg" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-baseline gap-2 mb-1">
                            <h3 className="font-serif text-xl font-bold truncate">{c.name}</h3>
                            <RoleBadge role={c.role} />
                          </div>
                          <div className="flex flex-wrap gap-1.5 text-[11px] text-muted-foreground">
                            {c.gender && <span>{c.gender}</span>}
                            {c.age && <span>· {c.age}</span>}
                          </div>
                        </div>
                      </div>

                      {c.personality && (
                        <p className="text-xs text-muted-foreground line-clamp-2 mb-3 italic">
                          {c.personality}
                        </p>
                      )}

                      {c.arc_summary && (
                        <div className="p-2 rounded bg-secondary/30 border border-border/40 mb-3">
                          <div className="text-[10px] text-lymo-gold-400 font-semibold tracking-wide mb-1">
                            弧线 · {c.arc_summary.current_phase || "发展中"}
                          </div>
                          <p className="text-[11px] text-muted-foreground line-clamp-2">
                            {c.arc_summary.emotional_trajectory || c.arc_summary.motivation || ""}
                          </p>
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-3 border-t border-border/40">
                        <span className="text-[11px] text-muted-foreground">
                          {c.relationships?.length || 0} 个关系
                        </span>
                        <ArrowRight className="size-3.5 text-muted-foreground group-hover:text-lymo-gold-400 group-hover:translate-x-1 transition-all" />
                      </div>
                    </div>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}

function RoleBadge({ role }: { role: string }) {
  if (role === "protagonist")
    return <Badge variant="gold" className="text-[9px] h-4 px-1.5">主角</Badge>;
  if (role === "antagonist")
    return <Badge variant="vermilion" className="text-[9px] h-4 px-1.5">反派</Badge>;
  return <Badge variant="stellar" className="text-[9px] h-4 px-1.5">配角</Badge>;
}

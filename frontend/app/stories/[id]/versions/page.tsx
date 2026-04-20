"use client";

import { use, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "motion/react";
import { History, GitBranch, ArrowDownToDot } from "lucide-react";
import dagre from "dagre";
import { Position } from "@xyflow/react";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  getChapterVersion,
  getVersionTree,
  restoreChapterVersion,
  type VersionTreeData,
  type VersionTreeVersion,
} from "@/lib/api";
import type { ChapterVersionDetail } from "@/types";
import { toast } from "sonner";

import "@xyflow/react/dist/style.css";

const ReactFlow = dynamic(() => import("@xyflow/react").then((m) => m.ReactFlow), {
  ssr: false,
  loading: () => <Skeleton className="h-[600px] w-full" />,
});
const Background = dynamic(() => import("@xyflow/react").then((m) => m.Background), { ssr: false });
const Controls = dynamic(() => import("@xyflow/react").then((m) => m.Controls), { ssr: false });

function VersionNode({ data }: any) {
  const v: VersionTreeVersion = data.version;
  const isLive = v.is_live === 1;
  const highlighted = data.highlighted;
  return (
    <button
      onClick={data.onClick}
      className={`w-full h-full px-3 py-2 text-left rounded-md border-2 transition-all ${
        highlighted
          ? "border-lymo-gold-500 glow-gold"
          : isLive
          ? "border-lymo-jade-500/70 bg-lymo-jade-500/5"
          : "border-border bg-card"
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="font-mono font-bold text-sm">v{v.version_num}</span>
        {isLive && <Badge variant="jade" className="text-[9px] h-4 px-1.5">LIVE</Badge>}
      </div>
      <div className="text-[11px] font-serif truncate leading-snug">
        {v.title || "(无标题)"}
      </div>
      <div className="text-[10px] text-muted-foreground mt-1 tabular-nums">
        {v.word_count.toLocaleString()} 字
      </div>
    </button>
  );
}

const nodeTypes = { version: VersionNode };

export default function VersionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: storyId } = use(params);
  const [tree, setTree] = useState<VersionTreeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ChapterVersionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const reload = async () => {
    setLoading(true);
    try {
      const t = await getVersionTree(storyId);
      setTree(t);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
  }, [storyId]);

  // Load detail when version selected
  useEffect(() => {
    if (!selectedVersionId || !tree) {
      setDetail(null);
      return;
    }
    // Find chapter for this version
    let chapterNum: number | null = null;
    for (const ch of tree.chapters) {
      if (ch.versions.some((v) => v.id === selectedVersionId)) {
        chapterNum = ch.chapter_num;
        break;
      }
    }
    if (!chapterNum) return;
    setDetailLoading(true);
    getChapterVersion(storyId, chapterNum, selectedVersionId)
      .then(setDetail)
      .catch(() => toast.error("加载版本失败"))
      .finally(() => setDetailLoading(false));
  }, [selectedVersionId, storyId, tree]);

  // Build graph layout
  const graph = useMemo(() => {
    if (!tree) return { nodes: [], edges: [] };

    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: "LR", nodesep: 30, ranksep: 100 });
    g.setDefaultEdgeLabel(() => ({}));

    const W = 160;
    const H = 80;

    const allVersions: VersionTreeVersion[] = [];
    tree.chapters.forEach((ch) => {
      ch.versions.forEach((v) => {
        allVersions.push(v);
        g.setNode(`v${v.id}`, { width: W, height: H });
      });
    });

    // Same-chapter evolution edges (version N -> N+1)
    tree.chapters.forEach((ch) => {
      const sorted = [...ch.versions].sort((a, b) => a.version_num - b.version_num);
      for (let i = 0; i < sorted.length - 1; i++) {
        g.setEdge(`v${sorted[i].id}`, `v${sorted[i + 1].id}`);
      }
    });

    // Dependency edges (ch2.v1 depends on ch1.v1) — only draw the live version's deps for clarity
    const liveByChapter = new Map<number, number>();
    tree.chapters.forEach((ch) => {
      const live = ch.versions.find((v) => v.is_live === 1);
      if (live) liveByChapter.set(ch.chapter_num, live.id);
    });

    const depEdges = tree.dependencies.filter(
      (d) => liveByChapter.get(d.chapter_num) === d.source_version_id
    );
    depEdges.forEach((d) => {
      g.setEdge(`v${d.depends_on_version_id}`, `v${d.source_version_id}`, { dep: true });
    });

    dagre.layout(g);

    // Find downstream chapters for selected version (highlight)
    const highlightedIds = new Set<number>();
    if (selectedVersionId) {
      highlightedIds.add(selectedVersionId);
      // Find any downstream that depends on selected
      tree.dependencies.forEach((d) => {
        if (d.depends_on_version_id === selectedVersionId) {
          highlightedIds.add(d.source_version_id);
        }
      });
    }

    const rfNodes = allVersions.map((v) => {
      const pos = g.node(`v${v.id}`);
      return {
        id: `v${v.id}`,
        position: { x: pos.x - W / 2, y: pos.y - H / 2 },
        data: {
          version: v,
          highlighted: highlightedIds.has(v.id),
          onClick: () => setSelectedVersionId(v.id),
        },
        type: "version",
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: { width: W, height: H, padding: 0, border: "none", background: "transparent" },
      };
    });

    const rfEdges: any[] = [];
    // Evolution edges
    tree.chapters.forEach((ch) => {
      const sorted = [...ch.versions].sort((a, b) => a.version_num - b.version_num);
      for (let i = 0; i < sorted.length - 1; i++) {
        rfEdges.push({
          id: `evo-${sorted[i].id}-${sorted[i + 1].id}`,
          source: `v${sorted[i].id}`,
          target: `v${sorted[i + 1].id}`,
          style: { stroke: "#2d3d4e", strokeDasharray: "5 4" },
        });
      }
    });
    // Dependency edges
    depEdges.forEach((d) => {
      const isHighlighted =
        highlightedIds.has(d.source_version_id) || highlightedIds.has(d.depends_on_version_id);
      rfEdges.push({
        id: `dep-${d.depends_on_version_id}-${d.source_version_id}`,
        source: `v${d.depends_on_version_id}`,
        target: `v${d.source_version_id}`,
        animated: isHighlighted,
        style: {
          stroke: isHighlighted ? "#d4a84b" : "#5aa67d",
          strokeWidth: isHighlighted ? 2 : 1,
          opacity: isHighlighted ? 1 : 0.5,
        },
      });
    });

    // Chapter group labels as decoration: add phantom nodes at chapter_num column head
    return { nodes: rfNodes, edges: rfEdges };
  }, [tree, selectedVersionId]);

  const selectedChapter = useMemo(() => {
    if (!selectedVersionId || !tree) return null;
    for (const ch of tree.chapters) {
      if (ch.versions.some((v) => v.id === selectedVersionId)) return ch;
    }
    return null;
  }, [selectedVersionId, tree]);

  const downstreamOfSelected = useMemo(() => {
    if (!tree || !selectedVersionId) return [];
    return tree.dependencies
      .filter((d) => d.depends_on_version_id === selectedVersionId)
      .map((d) => d.chapter_num);
  }, [tree, selectedVersionId]);

  const handleRestore = async (versionId: number) => {
    if (!selectedChapter) return;
    if (!confirm(`将第 ${selectedChapter.chapter_num} 章回滚到此版本？`)) return;
    try {
      await restoreChapterVersion(storyId, selectedChapter.chapter_num, versionId);
      toast.success("回滚成功");
      setSelectedVersionId(null);
      reload();
    } catch (e) {
      toast.error(`回滚失败：${(e as Error).message}`);
    }
  };

  return (
    <div className="px-8 py-6 max-w-7xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-serif text-3xl font-bold flex items-center gap-3 mb-2">
          <History className="size-7 text-lymo-jade-400" />
          版本树
        </h1>
        <p className="text-sm text-muted-foreground">
          章节版本演进 + 级联依赖 · 点击节点查看详情
        </p>
      </motion.div>

      <Card className="p-0 overflow-hidden">
        <div className="px-5 py-3 border-b border-border/40 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <GitBranch className="size-4 text-lymo-gold-400" />
            <span className="font-serif font-semibold text-sm">
              {tree?.chapters.length || 0} 章 ·{" "}
              {tree?.chapters.reduce((s, ch) => s + ch.versions.length, 0) || 0} 个版本
            </span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="w-4 h-px bg-lymo-ink-500 border-dashed" style={{ borderTop: "1.5px dashed #2d3d4e" }} />
              同章演进
            </span>
            <span className="flex items-center gap-1">
              <span className="w-4 h-px bg-lymo-jade-500" />
              依赖关系
            </span>
            <span className="flex items-center gap-1">
              <span className="size-3 rounded-sm border-2 border-lymo-jade-500" />
              当前 LIVE
            </span>
          </div>
        </div>
        <div style={{ height: 600 }}>
          {loading ? (
            <Skeleton className="h-full w-full" />
          ) : tree && tree.chapters.length > 0 ? (
            <ReactFlow
              nodes={graph.nodes as any}
              edges={graph.edges}
              nodeTypes={nodeTypes}
              fitView
              proOptions={{ hideAttribution: true }}
              nodesDraggable={false}
              nodesConnectable={false}
            >
              <Background color="#2d3d4e" gap={20} size={1} />
              <Controls position="bottom-right" showInteractive={false} />
            </ReactFlow>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              还没有任何章节版本
            </div>
          )}
        </div>
      </Card>

      {/* Detail sheet */}
      <Sheet open={!!selectedVersionId} onOpenChange={(o) => !o && setSelectedVersionId(null)}>
        <SheetContent side="right" className="w-[700px] sm:max-w-[700px] overflow-y-auto">
          {detailLoading ? (
            <Skeleton className="h-32" />
          ) : detail ? (
            <>
              <SheetHeader>
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline">第 {detail.chapter_num} 章</Badge>
                  <Badge variant="outline">v{detail.version_num}</Badge>
                </div>
                <SheetTitle className="font-serif text-2xl">{detail.title || "(无标题)"}</SheetTitle>
                <SheetDescription>
                  {detail.word_count.toLocaleString()} 字 ·{" "}
                  {new Date(detail.created_at).toLocaleString("zh-CN")}
                </SheetDescription>
              </SheetHeader>

              {detail.feedback && (
                <div className="mt-4 p-3 rounded-md bg-lymo-gold-500/10 border border-lymo-gold-500/30">
                  <div className="text-[10px] tracking-wider text-lymo-gold-400 uppercase font-semibold mb-1">
                    反馈
                  </div>
                  <p className="text-xs text-muted-foreground">{detail.feedback}</p>
                </div>
              )}

              {downstreamOfSelected.length > 0 && (
                <div className="mt-4 p-3 rounded-md bg-lymo-stellar-500/10 border border-lymo-stellar-500/30">
                  <div className="text-[10px] tracking-wider text-lymo-stellar-400 uppercase font-semibold mb-2 flex items-center gap-1">
                    <ArrowDownToDot className="size-3" />
                    下游依赖（{downstreamOfSelected.length}）
                  </div>
                  <p className="text-xs text-muted-foreground">
                    第 {[...new Set(downstreamOfSelected)].sort((a, b) => a - b).join("、")} 章依赖本版本的记忆。
                    重新生成本章会把这些章节的记忆标记为过期。
                  </p>
                </div>
              )}

              <div className="mt-5 flex gap-2">
                {!(tree?.chapters.find((ch) => ch.chapter_num === detail.chapter_num)?.versions.find((v) => v.id === detail.id)?.is_live) && (
                  <Button onClick={() => handleRestore(detail.id)} variant="default" size="sm">
                    回滚到此版本
                  </Button>
                )}
                <Button
                  onClick={() => setSelectedVersionId(null)}
                  variant="ghost"
                  size="sm"
                >
                  关闭
                </Button>
              </div>

              <div className="mt-6">
                <div className="text-xs text-muted-foreground mb-2">正文预览</div>
                <div
                  className="p-4 rounded-md bg-secondary/30 border border-border/40 text-sm leading-7 max-h-[400px] overflow-y-auto font-serif"
                  style={{ fontFamily: "var(--font-serif)" }}
                >
                  {detail.content.split("\n").slice(0, 30).map((p, i) => (
                    <p key={i} className="indent-6 mb-2">
                      {p}
                    </p>
                  ))}
                  {detail.content.split("\n").length > 30 && (
                    <p className="text-xs text-muted-foreground mt-3 text-center">
                      （仅显示前 30 段）
                    </p>
                  )}
                </div>
              </div>
            </>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}

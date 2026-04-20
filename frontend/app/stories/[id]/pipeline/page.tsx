"use client";

import { use, useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "motion/react";
import { Workflow, Info, RefreshCw } from "lucide-react";
import dagre from "dagre";

import { Position } from "@xyflow/react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { AgentChip } from "@/components/lymo/agent-chip";
import { getProgress } from "@/lib/api";

// ReactFlow SSR-disabled
const ReactFlow = dynamic(
  () => import("@xyflow/react").then((m) => m.ReactFlow),
  { ssr: false, loading: () => <Skeleton className="h-[500px] w-full" /> }
);
const Background = dynamic(
  () => import("@xyflow/react").then((m) => m.Background),
  { ssr: false }
);
const Controls = dynamic(
  () => import("@xyflow/react").then((m) => m.Controls),
  { ssr: false }
);

import "@xyflow/react/dist/style.css";

// Init pipeline nodes (8)
const INIT_NODES = [
  { id: "concept", label: "概念", agent: "concept", desc: "题材/基调/金手指" },
  { id: "world_build", label: "世界观", agent: "world_builder", desc: "背景/势力/体系" },
  { id: "character_design", label: "角色设计", agent: "character_designer", desc: "主角/反派/配角" },
  { id: "outline_plan", label: "大纲规划", agent: "outline_planner", desc: "分卷/初始冲突" },
  { id: "assemble_bible", label: "组装 Bible", agent: "", desc: "合并输出" },
  { id: "extract_characters", label: "角色提取", agent: "", desc: "展平角色列表" },
  { id: "init_world", label: "世界状态", agent: "", desc: "初始化时间轴" },
  { id: "init_world_book", label: "世界书", agent: "", desc: "关键词触发" },
];

// Chapter pipeline nodes (13)
const CHAPTER_NODES = [
  { id: "load_context", label: "加载上下文", agent: "", desc: "bible + world + chars" },
  { id: "world_advance", label: "世界推进", agent: "world", desc: "生成本章事件" },
  { id: "plot_plan", label: "剧情规划", agent: "planner", desc: "章节 beats" },
  { id: "camera_decide", label: "视角裁定", agent: "camera", desc: "POV + 可见事件" },
  { id: "build_context", label: "组装上下文", agent: "", desc: "L1/L2/L3 记忆" },
  { id: "load_memories", label: "加载记忆", agent: "", desc: "角色记忆/关系" },
  { id: "scene_split", label: "场景拆分", agent: "scene_splitter", desc: "2-5 场景" },
  { id: "write_scenes", label: "场景写作", agent: "scene_writer", desc: "逐场景生成 + 校验" },
  { id: "assemble_chapter", label: "组装章节", agent: "", desc: "场景合并" },
  { id: "consistency_check", label: "终检", agent: "consistency", desc: "整章一致性" },
  { id: "save_chapter", label: "保存", agent: "", desc: "落库 + 版本化" },
  { id: "save_with_warning", label: "保存(警告)", agent: "", desc: "有警告时" },
  { id: "extract_memories", label: "提取记忆", agent: "extractor", desc: "记忆+摘要+弧线" },
];

const INIT_EDGES: [string, string][] = [
  ["concept", "world_build"],
  ["world_build", "character_design"],
  ["character_design", "outline_plan"],
  ["outline_plan", "assemble_bible"],
  ["assemble_bible", "extract_characters"],
  ["extract_characters", "init_world"],
  ["init_world", "init_world_book"],
];

const CHAPTER_EDGES: [string, string][] = [
  ["load_context", "world_advance"],
  ["world_advance", "plot_plan"],
  ["plot_plan", "camera_decide"],
  ["camera_decide", "build_context"],
  ["build_context", "load_memories"],
  ["load_memories", "scene_split"],
  ["scene_split", "write_scenes"],
  ["write_scenes", "assemble_chapter"],
  ["assemble_chapter", "consistency_check"],
  ["consistency_check", "save_chapter"],
  ["consistency_check", "save_with_warning"],
  ["consistency_check", "write_scenes"], // retry loop
  ["save_chapter", "extract_memories"],
  ["save_with_warning", "extract_memories"],
];

function layoutDag(
  nodes: { id: string; label: string; agent: string; desc: string }[],
  edges: [string, string][],
  direction: "LR" | "TB" = "LR",
  runtimeStatus?: Record<string, string>
) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: direction, nodesep: 50, ranksep: 80 });
  g.setDefaultEdgeLabel(() => ({}));

  const W = 200,
    H = 80;
  nodes.forEach((n) => g.setNode(n.id, { width: W, height: H }));
  edges.forEach(([s, t]) => g.setEdge(s, t));
  dagre.layout(g);

  const rfNodes = nodes.map((n) => {
    const pos = g.node(n.id);
    const status = runtimeStatus?.[n.id];
    const accent =
      status === "running"
        ? "border-lymo-gold-500 glow-gold"
        : status === "done"
        ? "border-lymo-jade-500/70"
        : status === "error"
        ? "border-destructive"
        : "border-border";
    return {
      id: n.id,
      position: { x: pos.x - W / 2, y: pos.y - H / 2 },
      data: { label: n, status },
      type: "custom",
      sourcePosition: direction === "LR" ? Position.Right : Position.Bottom,
      targetPosition: direction === "LR" ? Position.Left : Position.Top,
      className: `bg-card ${accent} rounded-md shadow-sm`,
      style: { width: W, height: H },
    };
  });

  const rfEdges = edges.map(([s, t], i) => ({
    id: `e-${s}-${t}-${i}`,
    source: s,
    target: t,
    animated: runtimeStatus?.[s] === "done" && runtimeStatus?.[t] === "running",
    style: {
      stroke: runtimeStatus?.[s] === "done" ? "#d4a84b" : "#2d3d4e",
      strokeWidth: 1.5,
    },
  }));

  return { nodes: rfNodes, edges: rfEdges };
}

function PipelineNode({ data }: any) {
  const node = data.label;
  return (
    <div className="px-3 py-2 h-full flex flex-col justify-center">
      <div className="flex items-center justify-between mb-1 gap-2">
        <span className="font-serif font-bold text-sm truncate">{node.label}</span>
        {node.agent && <AgentChip name={node.agent} />}
      </div>
      <div className="text-[10px] text-muted-foreground line-clamp-2">
        {node.desc}
      </div>
      {data.status && (
        <div
          className={`mt-1 text-[9px] font-semibold tracking-wide uppercase ${
            data.status === "running"
              ? "text-lymo-gold-400"
              : data.status === "done"
              ? "text-lymo-jade-400"
              : data.status === "error"
              ? "text-destructive"
              : "text-muted-foreground"
          }`}
        >
          {data.status}
        </div>
      )}
    </div>
  );
}

const nodeTypes = { custom: PipelineNode };

export default function PipelinePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: storyId } = use(params);
  const [progress, setProgress] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchProgress = useCallback(async () => {
    try {
      const p = await getProgress(storyId);
      setProgress(p);
    } catch {
      setProgress(null);
    } finally {
      setLoading(false);
    }
  }, [storyId]);

  useEffect(() => {
    fetchProgress();
    const t = setInterval(fetchProgress, 3000);
    return () => clearInterval(t);
  }, [fetchProgress]);

  const runtimeStatus = useMemo(() => {
    if (!progress?.stages) return {};
    const map: Record<string, string> = {};
    progress.stages.forEach((s: any) => {
      map[s.name] = s.status;
    });
    return map;
  }, [progress]);

  const initGraph = useMemo(() => layoutDag(INIT_NODES, INIT_EDGES, "LR"), []);
  const chapterGraph = useMemo(
    () => layoutDag(CHAPTER_NODES, CHAPTER_EDGES, "LR", runtimeStatus),
    [runtimeStatus]
  );

  return (
    <div className="px-8 py-6 max-w-7xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="font-serif text-3xl font-bold flex items-center gap-3">
              <Workflow className="size-7 text-lymo-stellar-400" />
              生成管线
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              LangGraph 多智能体协作流程 · 实时状态
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={fetchProgress}>
            <RefreshCw className="size-3.5" />
            刷新
          </Button>
        </div>
      </motion.div>

      {/* Live progress strip */}
      {progress?.current_stage && (
        <Card className="p-4 border-lymo-gold-500/40">
          <div className="flex items-center gap-3">
            <div className="size-3 rounded-full bg-lymo-gold-500 animate-pulse" />
            <div className="flex-1">
              <div className="text-sm font-serif font-semibold text-lymo-gold-400">
                {progress.current_stage_label || progress.current_stage}
              </div>
              <div className="text-xs text-muted-foreground">
                已运行 {Math.round(progress.elapsed_seconds)} 秒
              </div>
            </div>
            <Badge variant="gold">RUNNING</Badge>
          </div>
        </Card>
      )}

      <Tabs defaultValue="chapter">
        <TabsList>
          <TabsTrigger value="chapter">章节管线（13 节点）</TabsTrigger>
          <TabsTrigger value="init">初始化管线（8 节点）</TabsTrigger>
        </TabsList>

        <TabsContent value="chapter">
          <Card className="p-0 overflow-hidden">
            <div className="px-5 py-3 border-b border-border/40 flex items-center justify-between">
              <div>
                <div className="font-serif font-semibold text-sm">Chapter Graph</div>
                <div className="text-[11px] text-muted-foreground">
                  生成一章完整流程；失败时 consistency_check → write_scenes 循环重试
                </div>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <span className="size-2 rounded-full bg-lymo-gold-500" />
                  运行中
                </span>
                <span className="flex items-center gap-1">
                  <span className="size-2 rounded-full bg-lymo-jade-500" />
                  已完成
                </span>
                <span className="flex items-center gap-1">
                  <span className="size-2 rounded-full bg-lymo-ink-600" />
                  待运行
                </span>
              </div>
            </div>
            <div style={{ height: 600 }}>
              {loading ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <ReactFlow
                  nodes={chapterGraph.nodes as any}
                  edges={chapterGraph.edges}
                  nodeTypes={nodeTypes}
                  fitView
                  proOptions={{ hideAttribution: true }}
                  nodesDraggable={false}
                  nodesConnectable={false}
                >
                  <Background color="#2d3d4e" gap={20} size={1} />
                  <Controls position="bottom-right" showInteractive={false} />
                </ReactFlow>
              )}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="init">
          <Card className="p-0 overflow-hidden">
            <div className="px-5 py-3 border-b border-border/40">
              <div className="font-serif font-semibold text-sm">Init Graph</div>
              <div className="text-[11px] text-muted-foreground">
                新故事启动时运行一次，产出完整 StoryBible
              </div>
            </div>
            <div style={{ height: 500 }}>
              <ReactFlow
                nodes={initGraph.nodes as any}
                edges={initGraph.edges}
                nodeTypes={nodeTypes}
                fitView
                proOptions={{ hideAttribution: true }}
                nodesDraggable={false}
                nodesConnectable={false}
              >
                <Background color="#2d3d4e" gap={20} size={1} />
                <Controls position="bottom-right" showInteractive={false} />
              </ReactFlow>
            </div>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Stage list */}
      {progress?.stages && (
        <Card className="p-5">
          <h3 className="font-serif font-semibold mb-4 flex items-center gap-2">
            <Info className="size-4 text-lymo-stellar-400" />
            阶段详情
          </h3>
          <div className="space-y-1.5">
            {progress.stages.map((s: any) => (
              <div
                key={s.name}
                className="flex items-center gap-3 text-xs p-2 rounded-md bg-secondary/20"
              >
                <span
                  className={`size-2 rounded-full ${
                    s.status === "running"
                      ? "bg-lymo-gold-500 animate-pulse"
                      : s.status === "done"
                      ? "bg-lymo-jade-500"
                      : s.status === "error"
                      ? "bg-destructive"
                      : "bg-lymo-ink-600"
                  }`}
                />
                <span className="font-serif font-medium w-32 truncate">{s.label}</span>
                <span className="flex-1 text-muted-foreground truncate">{s.detail || "-"}</span>
                {s.duration_ms > 0 && (
                  <span className="text-muted-foreground tabular-nums">
                    {(s.duration_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

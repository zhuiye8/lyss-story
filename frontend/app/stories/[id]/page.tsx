"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import {
  Sparkles,
  FileText,
  Clock,
  Trash2,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Feather,
  Square,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { ScoreRing } from "@/components/lymo/score-ring";
import { CharacterAvatar } from "@/components/lymo/character-avatar";
import {
  cancelGeneration,
  deleteStory,
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
import type { StoryResponse, ChapterSummary } from "@/types";
import PipelineProgress from "@/components/PipelineProgress";

const CHAPTER_SIZE_OPTIONS = [
  { value: 1500, label: "短章", scenes: 2, desc: "~1500字 · 2个场景 · 快节奏推进" },
  { value: 2500, label: "标准", scenes: 3, desc: "~2500字 · 3个场景 · 均衡叙事" },
  { value: 3000, label: "长章", scenes: 4, desc: "~3000字 · 4个场景 · 深度展开" },
  { value: 4000, label: "超长", scenes: 5, desc: "~4000字 · 5个场景 · 最大篇幅" },
];

function StatusPill({ status, currentChapter, errorMessage }: { status: string; currentChapter: number | null; errorMessage: string | null; }) {
  const base = "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border";
  if (status === "generating")
    return (
      <div className={`${base} bg-lymo-gold-500/10 text-lymo-gold-400 border-lymo-gold-500/30`}>
        <Loader2 className="size-3 animate-spin" />
        生成第 {currentChapter} 章
      </div>
    );
  if (status === "initializing")
    return (
      <div className={`${base} bg-lymo-stellar-500/10 text-lymo-stellar-400 border-lymo-stellar-500/30`}>
        <Loader2 className="size-3 animate-spin" />
        初始化中
      </div>
    );
  if (status === "bible_ready")
    return (
      <div className={`${base} bg-lymo-jade-500/10 text-lymo-jade-400 border-lymo-jade-500/30`}>
        <CheckCircle2 className="size-3" />
        就绪
      </div>
    );
  if (status.startsWith("error"))
    return (
      <div className={`${base} bg-destructive/15 text-destructive border-destructive/30`} title={errorMessage || status}>
        <AlertCircle className="size-3" />
        异常
      </div>
    );
  return (
    <div className={`${base} bg-muted text-muted-foreground border-border`}>
      {status}
    </div>
  );
}

export default function StoryDashboard({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: storyId } = use(params);
  const router = useRouter();
  const [story, setStory] = useState<StoryResponse | null>(null);
  const [bible, setBible] = useState<any | null>(null);
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [status, setStatus] = useState("loading");
  const [currentChapter, setCurrentChapter] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isTaskRunning, setIsTaskRunning] = useState(false);
  const [progress, setProgress] = useState<GenerationProgressData | null>(null);
  const [wordCount, setWordCount] = useState(3000);
  const [genDialogOpen, setGenDialogOpen] = useState(false);

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
      setIsTaskRunning(!!st.is_task_running);

      if (st.status === "generating") {
        try {
          const p = await getProgress(storyId);
          setProgress(p);
        } catch {
          /* ignore */
        }
      }

      if (s.status !== "initializing") {
        try {
          const b = await getStoryBible(storyId);
          setBible(b);
        } catch {
          /* ignore */
        }
      }
    } catch (e) {
      console.error(e);
    }
  }, [storyId]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, status === "generating" ? 1500 : 4000);
    return () => clearInterval(interval);
  }, [refresh, status]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setProgress(null);
    setGenDialogOpen(false);
    try {
      await triggerGeneration(storyId, wordCount);
      toast.success(`开始生成，目标 ${wordCount} 字`);
    } catch (e) {
      toast.error(`启动失败：${(e as Error).message}`);
    } finally {
      setTimeout(() => setIsGenerating(false), 2000);
    }
  };

  const handleCancel = async () => {
    if (!confirm("确认停止当前生成任务？正在进行的 LLM 调用会被中断。")) return;
    setIsCancelling(true);
    try {
      const res = await cancelGeneration(storyId);
      toast.success(res.message || "已停止");
      setTimeout(() => {
        refresh();
        setIsCancelling(false);
      }, 800);
    } catch (e) {
      toast.error(`停止失败：${(e as Error).message}`);
      setIsCancelling(false);
    }
  };

  const handleDelete = async () => {
    if (!story) return;
    if (!confirm(`确认删除《${story.title || story.theme}》？不可恢复。`)) return;
    try {
      await deleteStory(storyId);
      toast.success("已删除");
      router.push("/");
    } catch {
      toast.error("删除失败");
    }
  };

  const canGenerate = ["bible_ready", "completed"].includes(status) || status.startsWith("error");
  const lastChapter = chapters[chapters.length - 1];
  const totalWords = chapters.reduce((sum, c) => sum + (c.word_count || 0), 0);
  const warnings = chapters.filter((c) => c.has_warnings).length;

  const flatChars = bible
    ? [
        bible.protagonist,
        bible.antagonist,
        ...(bible.supporting_characters || []),
      ].filter(Boolean)
    : [];

  if (!story) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-6">
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
        <div className="grid md:grid-cols-3 gap-4 mt-6">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="px-8 py-6 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-start justify-between mb-2">
          <div className="min-w-0">
            <h1 className="font-serif text-3xl md:text-4xl font-bold truncate">
              《{story.title || "未命名"}》
            </h1>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2 max-w-2xl">
              {story.theme}
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                await publishStory(storyId, !story.is_published);
                refresh();
              }}
            >
              {story.is_published ? (
                <>
                  <Eye className="size-3.5" />
                  已发布
                </>
              ) : (
                <>
                  <EyeOff className="size-3.5" />
                  发布
                </>
              )}
            </Button>
            <Button variant="ghost" size="sm" onClick={handleDelete}>
              <Trash2 className="size-3.5" />
            </Button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <StatusPill
            status={status}
            currentChapter={currentChapter}
            errorMessage={errorMessage}
          />

          {(status === "generating" || status === "initializing" || isTaskRunning) && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCancel}
              disabled={isCancelling}
            >
              {isCancelling ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  停止中...
                </>
              ) : (
                <>
                  <Square className="size-3.5" />
                  停止生成
                </>
              )}
            </Button>
          )}

          <Dialog open={genDialogOpen} onOpenChange={setGenDialogOpen}>
            <DialogTrigger asChild>
              <Button
                disabled={!canGenerate || isGenerating || status === "generating" || status === "initializing" || isTaskRunning}
                size="sm"
                className="font-serif"
              >
                <Sparkles className="size-3.5" />
                生成下一章
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="font-serif">生成第 {chapters.length + 1} 章</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label className="mb-2 block">章节规模</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {CHAPTER_SIZE_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setWordCount(opt.value)}
                        className={`text-left p-3 rounded-lg border transition-all ${
                          wordCount === opt.value
                            ? "bg-primary/10 border-primary glow-vermilion"
                            : "bg-transparent border-border hover:bg-secondary/50"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-serif font-bold">{opt.label}</span>
                          <Badge variant={wordCount === opt.value ? "gold" : "ghost"} className="text-[10px]">
                            {opt.scenes} 场景
                          </Badge>
                        </div>
                        <p className="text-[11px] text-muted-foreground">{opt.desc}</p>
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-3">
                    每个场景独立生成 + 独立校验，场景越多叙事越丰富但调用次数越多。
                    最终字数由 AI 在目标范围内自主把控，不做硬截断。
                  </p>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={handleGenerate} variant="default" className="font-serif">
                  <Feather className="size-4" />
                  启动生成
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </motion.div>

      {/* Pipeline progress (when generating) */}
      {(status === "generating" || progress?.stages?.some((s) => s.status !== "pending")) && (
        <Card className="p-4 mb-6">
          <PipelineProgress progress={progress} />
        </Card>
      )}

      {/* Stats strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatsCard label="章节数" value={chapters.length} icon={<FileText className="size-4" />} />
        <StatsCard label="总字数" value={totalWords.toLocaleString()} icon={<Feather className="size-4" />} />
        <StatsCard label="角色数" value={flatChars.length} icon={<Sparkles className="size-4" />} />
        <StatsCard
          label="警告"
          value={warnings}
          icon={<AlertCircle className="size-4" />}
          variant={warnings > 0 ? "warn" : "ok"}
        />
      </div>

      {/* Dashboard grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: snapshot (bible summary + characters preview) */}
        <div className="lg:col-span-2 space-y-6">
          {bible && (
            <Card className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-serif text-lg font-bold">作品设定</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    {bible.genre} · {bible.tone || "无基调"}
                  </p>
                </div>
                <Link href={`/stories/${storyId}/outline`}>
                  <Button variant="outline" size="sm">
                    编辑大纲
                  </Button>
                </Link>
              </div>
              {bible.one_line_summary && (
                <p className="text-sm mb-3 font-serif italic text-muted-foreground border-l-2 border-lymo-gold-500/40 pl-3">
                  "{bible.one_line_summary}"
                </p>
              )}
              {bible.synopsis && (
                <p className="text-sm leading-relaxed line-clamp-4 mb-4">
                  {bible.synopsis}
                </p>
              )}
              {bible.world?.special_ability?.name && (
                <div className="mt-3 p-3 rounded-md bg-lymo-gold-500/5 border border-lymo-gold-500/30">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] text-lymo-gold-400 font-semibold tracking-wider uppercase">
                      金手指
                    </span>
                    <span className="font-serif font-bold text-lymo-gold-400">
                      {bible.world.special_ability.name}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {bible.world.special_ability.description}
                  </p>
                </div>
              )}
            </Card>
          )}

          {/* Recent chapters */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-serif text-lg font-bold">最近章节</h3>
              <Link href={`/stories/${storyId}/insights`}>
                <Button variant="ghost" size="sm">
                  查看全部 ({chapters.length})
                </Button>
              </Link>
            </div>
            {chapters.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                还未生成任何章节
              </p>
            ) : (
              <div className="space-y-2">
                {chapters.slice(-5).reverse().map((ch) => (
                  <Link
                    key={ch.chapter_num}
                    href={`/stories/${storyId}/chapters/${ch.chapter_num}`}
                    className="flex items-center gap-3 p-3 rounded-md hover:bg-secondary/50 transition group"
                  >
                    <Badge variant="outline" className="w-14 justify-center tabular-nums font-mono">
                      {ch.chapter_num.toString().padStart(2, "0")}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <div className="font-serif font-medium truncate group-hover:text-foreground">
                        {ch.title || `第 ${ch.chapter_num} 章`}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                        <span className="tabular-nums">{ch.word_count.toLocaleString()} 字</span>
                        <span>·</span>
                        <span className="truncate">{ch.pov || "未指定视角"}</span>
                        {ch.has_warnings && (
                          <Badge variant="destructive" className="text-[9px] h-4 px-1.5">警告</Badge>
                        )}
                        {ch.is_published && (
                          <Badge variant="jade" className="text-[9px] h-4 px-1.5">已发布</Badge>
                        )}
                      </div>
                    </div>
                    <Clock className="size-3.5 text-muted-foreground group-hover:text-foreground transition" />
                  </Link>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right: characters preview */}
        <div className="space-y-6">
          {flatChars.length > 0 && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-serif text-lg font-bold">角色</h3>
                <Link href={`/stories/${storyId}/characters`}>
                  <Button variant="ghost" size="sm">
                    查看
                  </Button>
                </Link>
              </div>
              <div className="space-y-3">
                {flatChars.slice(0, 5).map((c: any) => (
                  <Link
                    key={c.character_id}
                    href={`/stories/${storyId}/characters/${encodeURIComponent(c.character_id)}`}
                    className="flex items-center gap-3 group"
                  >
                    <CharacterAvatar name={c.name} role={c.role} size="md" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate group-hover:text-foreground">{c.name}</div>
                      <div className="text-[10px] text-muted-foreground line-clamp-1">
                        {c.personality || c.role}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </Card>
          )}

          {/* Volume progress */}
          {bible?.volumes?.length > 0 && (
            <Card className="p-6">
              <h3 className="font-serif text-lg font-bold mb-4">分卷进度</h3>
              <div className="space-y-3">
                {bible.volumes.map((v: any, i: number) => {
                  const start = v.chapter_start || 1;
                  const end = v.chapter_end || start;
                  const total = end - start + 1;
                  const done = chapters.filter(
                    (c) => c.chapter_num >= start && c.chapter_num <= end
                  ).length;
                  const pct = total > 0 ? Math.min(100, (done / total) * 100) : 0;
                  return (
                    <div key={i}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-serif font-medium truncate">
                          第{v.volume_num}卷 · {v.volume_name}
                        </span>
                        <span className="text-muted-foreground tabular-nums">
                          {done}/{total}
                        </span>
                      </div>
                      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-vermilion-grad transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Continue writing banner */}
          {lastChapter && canGenerate && (
            <Card className="p-5 bg-gradient-to-br from-lymo-ink-800 to-lymo-ink-700 border-lymo-gold-500/30">
              <div className="flex items-center gap-3 mb-3">
                <Feather className="size-5 text-lymo-gold-400" />
                <div>
                  <div className="text-xs text-muted-foreground">上次写到</div>
                  <div className="font-serif font-medium text-sm">
                    第 {lastChapter.chapter_num} 章 · {lastChapter.title}
                  </div>
                </div>
              </div>
              <Button
                size="sm"
                className="w-full font-serif"
                onClick={() => setGenDialogOpen(true)}
              >
                继续下一章
              </Button>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function StatsCard({
  label,
  value,
  icon,
  variant = "default",
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  variant?: "default" | "warn" | "ok";
}) {
  const accentColor =
    variant === "warn"
      ? "text-lymo-vermilion-400"
      : variant === "ok"
      ? "text-lymo-jade-400"
      : "text-lymo-gold-400";
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className={accentColor}>{icon}</span>
      </div>
      <div className="font-serif text-2xl font-bold tabular-nums">{value}</div>
    </Card>
  );
}

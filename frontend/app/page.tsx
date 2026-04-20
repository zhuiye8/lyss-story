"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import { BookOpenText, Sparkles, Upload, ArrowRight, FileText, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Mascot } from "@/components/lymo/mascot";
import { createStory, deleteStory, importOutline, listStories } from "@/lib/api";
import type { StoryResponse } from "@/types";

function StatusBadge({ status }: { status: string }) {
  if (status === "bible_ready")
    return <Badge variant="jade">就绪</Badge>;
  if (status === "generating")
    return <Badge variant="gold">生成中</Badge>;
  if (status === "initializing")
    return <Badge variant="stellar">初始化</Badge>;
  if (status === "awaiting_outline")
    return <Badge variant="outline">待导入</Badge>;
  if (status.startsWith("error"))
    return <Badge variant="destructive">错误</Badge>;
  return <Badge variant="ghost">{status}</Badge>;
}

export default function HomePage() {
  const router = useRouter();
  const [stories, setStories] = useState<StoryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [mode, setMode] = useState<"ai" | "import">("ai");

  // form state
  const [theme, setTheme] = useState("");
  const [requirements, setRequirements] = useState("");
  const [title, setTitle] = useState("");
  const [importTitle, setImportTitle] = useState("");
  const [importText, setImportText] = useState("");

  const reload = async () => {
    try {
      const data = await listStories();
      setStories(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
  }, []);

  const handleAICreate = async () => {
    if (!theme.trim()) {
      toast.error("请至少填写题材或创作要求");
      return;
    }
    setSubmitting(true);
    try {
      const story = await createStory(theme, requirements, title);
      toast.success(`《${title || theme.slice(0, 10)}》已启动构思`);
      router.push(`/stories/${story.story_id}`);
    } catch (e) {
      toast.error(`创建失败：${(e as Error).message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleImport = async () => {
    if (!importText.trim()) {
      toast.error("请粘贴大纲文本");
      return;
    }
    setSubmitting(true);
    try {
      const story = await createStory(
        importTitle || "待解析大纲",
        "",
        importTitle,
        true
      );
      await importOutline(story.story_id, importText.trim(), importTitle.trim());
      toast.success("大纲解析中，即将跳转...");
      router.push(`/stories/${story.story_id}`);
    } catch (e) {
      toast.error(`导入失败：${(e as Error).message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, story: StoryResponse) => {
    e.stopPropagation();
    if (!confirm(`确认删除《${story.title || story.theme}》？不可恢复。`)) return;
    try {
      await deleteStory(story.story_id);
      toast.success("已删除");
      setStories((prev) => prev.filter((s) => s.story_id !== story.story_id));
    } catch {
      toast.error("删除失败");
    }
  };

  return (
    <div className="relative">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 star-field opacity-40" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,var(--lymo-ink-900)_100%)]" />
        <div className="relative max-w-7xl mx-auto px-6 pt-16 pb-24 md:pt-24 md:pb-32">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              className="space-y-6"
            >
              <Badge variant="gold" className="font-serif">
                · 狸梦 Lymo · AI 小说宇宙 ·
              </Badge>
              <h1 className="font-serif text-5xl md:text-6xl font-bold leading-tight tracking-tight">
                <span className="text-gold-grad">开启你的</span>
                <br />
                <span className="text-foreground">小说宇宙</span>
              </h1>
              <p className="text-lg text-muted-foreground max-w-xl leading-relaxed">
                从一句话到一部长篇，<span className="text-lymo-vermilion-300">6 个 AI 智能体</span>
                与你协作。
                世界观、角色、剧情、笔法、一致性—— 全由狸梦为你照看。
              </p>
              <div className="flex flex-wrap gap-3 pt-2">
                <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="lg" variant="default" className="font-serif">
                      <Sparkles className="size-4" />
                      开始创作
                      <ArrowRight className="size-4" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle className="font-serif text-2xl">创建新的小说</DialogTitle>
                      <DialogDescription>
                        让 AI 从零构思，或导入你已有的大纲开始。
                      </DialogDescription>
                    </DialogHeader>

                    <Tabs value={mode} onValueChange={(v) => setMode(v as "ai" | "import")}>
                      <TabsList className="grid grid-cols-2 w-full">
                        <TabsTrigger value="ai">
                          <Sparkles className="size-4 mr-1.5" /> AI 生成
                        </TabsTrigger>
                        <TabsTrigger value="import">
                          <Upload className="size-4 mr-1.5" /> 导入大纲
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="ai" className="space-y-4">
                        <div className="space-y-2">
                          <Label>书名（可选）</Label>
                          <Input
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="留空由 AI 起名"
                            disabled={submitting}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>题材</Label>
                          <Input
                            value={theme}
                            onChange={(e) => setTheme(e.target.value)}
                            placeholder="例如：末世、修真、都市、科幻、无限流…"
                            disabled={submitting}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>创作要求（可选）</Label>
                          <Textarea
                            value={requirements}
                            onChange={(e) => setRequirements(e.target.value)}
                            rows={5}
                            placeholder="例：主角冷静理智，有金手指能操控数据；世界观为赛博朋克 + 修真；反派是上古残魂..."
                            disabled={submitting}
                          />
                        </div>
                        <Button
                          onClick={handleAICreate}
                          disabled={submitting || !theme.trim()}
                          size="lg"
                          className="w-full font-serif"
                        >
                          {submitting ? "狸梦正在构思..." : "启动 4 步智能构思"}
                        </Button>
                      </TabsContent>

                      <TabsContent value="import" className="space-y-4">
                        <div className="space-y-2">
                          <Label>书名（可选）</Label>
                          <Input
                            value={importTitle}
                            onChange={(e) => setImportTitle(e.target.value)}
                            placeholder="例如：末世数据师"
                            disabled={submitting}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>
                            粘贴大纲 <span className="text-destructive">*</span>
                          </Label>
                          <Textarea
                            value={importText}
                            onChange={(e) => setImportText(e.target.value)}
                            rows={12}
                            placeholder={
                              "在此粘贴你的大纲文本...\n\n支持任意格式：\n- 网文平台的大纲模板\n- 自己写的笔记\n- 世界观 + 角色 + 剧情大纲"
                            }
                            className="font-mono text-xs"
                            disabled={submitting}
                          />
                          <p className="text-xs text-muted-foreground">
                            规则解析 + AI 补全：保留你的原文，只补齐缺失字段。
                          </p>
                        </div>
                        <Button
                          onClick={handleImport}
                          disabled={submitting || !importText.trim()}
                          variant="gold"
                          size="lg"
                          className="w-full font-serif"
                        >
                          {submitting ? "解析中..." : "导入并解析"}
                        </Button>
                      </TabsContent>
                    </Tabs>
                  </DialogContent>
                </Dialog>

                {stories.length > 0 && (
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={() => {
                      document.getElementById("my-stories")?.scrollIntoView({ behavior: "smooth" });
                    }}
                  >
                    <BookOpenText className="size-4" />
                    我的书斋（{stories.length}）
                  </Button>
                )}
              </div>

              {/* Feature strip */}
              <div className="grid grid-cols-3 gap-3 pt-6 max-w-lg">
                {[
                  { label: "4 步构思", hint: "概念·世界·角色·大纲" },
                  { label: "场景级写作", hint: "500 字一场永不漂移" },
                  { label: "3D 角色宇宙", hint: "视觉呈现关系网" },
                ].map((f) => (
                  <div
                    key={f.label}
                    className="text-center p-3 rounded-lg bg-card/40 border border-border/40 backdrop-blur"
                  >
                    <div className="text-xs font-semibold text-lymo-gold-400">{f.label}</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">{f.hint}</div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Mascot side */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative flex justify-center items-center"
            >
              {/* Soft glow behind */}
              <div className="absolute w-80 h-80 bg-lymo-vermilion-500/10 rounded-full blur-3xl" />
              <div className="absolute w-60 h-60 bg-lymo-gold-500/10 rounded-full blur-3xl" />
              <motion.div
                animate={{
                  y: [0, -10, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="relative"
              >
                <Mascot variant="cheering" size={360} priority className="drop-shadow-[0_20px_40px_rgba(212,168,75,0.25)]" />
              </motion.div>
              <div className="absolute top-4 right-4 px-3 py-1.5 rounded-full bg-card/80 backdrop-blur border border-border text-xs font-serif text-lymo-gold-400">
                狸梦在此
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stories list */}
      <section id="my-stories" className="max-w-7xl mx-auto px-6 pb-24">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="font-serif text-2xl font-bold">我的书斋</h2>
            <p className="text-sm text-muted-foreground mt-1">
              {loading ? "加载中..." : `共 ${stories.length} 部作品`}
            </p>
          </div>
          <Button
            onClick={() => setDialogOpen(true)}
            variant="outline"
          >
            <Plus className="size-4" />
            新建
          </Button>
        </div>

        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-40" />
            ))}
          </div>
        ) : stories.length === 0 ? (
          <Card className="p-16 text-center">
            <Mascot variant="sad-pleading" size={120} className="mx-auto mb-4 opacity-80" />
            <p className="text-muted-foreground font-serif">书斋空空如也，点"开始创作"写下第一笔。</p>
          </Card>
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
            {stories.map((s) => (
              <motion.div
                key={s.story_id}
                variants={{
                  hidden: { opacity: 0, y: 10 },
                  show: { opacity: 1, y: 0 },
                }}
              >
                <Card
                  className="p-5 card-hover cursor-pointer relative group overflow-hidden"
                  onClick={() => router.push(`/stories/${s.story_id}`)}
                >
                  {/* Accent side bar */}
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-vermilion-grad opacity-70 group-hover:opacity-100 transition-opacity" />

                  <div className="flex items-start justify-between mb-3">
                    <StatusBadge status={s.status} />
                    <button
                      onClick={(e) => handleDelete(e, s)}
                      className="opacity-0 group-hover:opacity-70 hover:!opacity-100 transition-opacity p-1 rounded text-muted-foreground hover:text-destructive"
                      title="删除"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>

                  <h3 className="font-serif text-lg font-bold mb-1 line-clamp-1">
                    {s.title || "（未命名）"}
                  </h3>
                  <p className="text-xs text-muted-foreground line-clamp-2 h-8 mb-3">
                    {s.theme}
                  </p>

                  <div className="flex items-center justify-between pt-3 border-t border-border/40">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <FileText className="size-3.5" />
                      <span>{s.chapter_count} 章</span>
                    </div>
                    {s.is_published && (
                      <Badge variant="jade">已发布</Badge>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}
      </section>
    </div>
  );
}

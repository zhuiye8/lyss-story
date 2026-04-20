"use client";

import { useCallback, useEffect, useState, use } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { ArrowLeft, ArrowRight, History, AlertTriangle, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { getChapter } from "@/lib/api";
import type { ChapterDetail } from "@/types";
import ChapterVersionPanel from "@/components/ChapterVersionPanel";

export default function ChapterPage({
  params,
}: {
  params: Promise<{ id: string; num: string }>;
}) {
  const { id: storyId, num } = use(params);
  const chapterNum = parseInt(num, 10);
  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [versionsOpen, setVersionsOpen] = useState(false);

  const reload = useCallback(() => {
    getChapter(storyId, chapterNum)
      .then(setChapter)
      .catch((e) => setError(e.message));
  }, [storyId, chapterNum]);

  useEffect(() => {
    reload();
  }, [reload]);

  if (error) {
    return (
      <div className="px-8 py-10 max-w-3xl mx-auto">
        <p className="text-destructive mb-3">加载失败：{error}</p>
        <Link href={`/stories/${storyId}`} className="text-primary hover:underline text-sm">
          返回故事
        </Link>
      </div>
    );
  }

  if (!chapter) {
    return (
      <div className="px-8 py-10 max-w-3xl mx-auto space-y-4">
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-4 w-1/3" />
        <div className="space-y-2 pt-6">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-4" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-56px)]">
      {/* Top nav */}
      <div className="sticky top-14 z-30 bg-background/80 backdrop-blur border-b border-border/40">
        <div className="max-w-3xl mx-auto px-6 h-12 flex items-center justify-between">
          <Link
            href={`/stories/${storyId}`}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition"
          >
            <ArrowLeft className="size-3.5" />
            返回故事
          </Link>
          <div className="flex items-center gap-1">
            {chapterNum > 1 && (
              <Link href={`/stories/${storyId}/chapters/${chapterNum - 1}`}>
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="size-3.5" />
                  上一章
                </Button>
              </Link>
            )}
            <Link href={`/stories/${storyId}/chapters/${chapterNum + 1}`}>
              <Button variant="ghost" size="sm">
                下一章
                <ArrowRight className="size-3.5" />
              </Button>
            </Link>
            <Sheet open={versionsOpen} onOpenChange={setVersionsOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm">
                  <History className="size-3.5" />
                  版本与重写
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[520px] sm:max-w-[520px] overflow-y-auto">
                <SheetHeader className="mb-4">
                  <SheetTitle className="font-serif text-xl">版本与重写</SheetTitle>
                </SheetHeader>
                <ChapterVersionPanel
                  storyId={storyId}
                  chapterNum={chapterNum}
                  onRestored={() => {
                    reload();
                    setVersionsOpen(false);
                  }}
                />
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>

      {/* Chapter content */}
      <motion.article
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl mx-auto px-6 py-10"
      >
        {/* Chapter header */}
        <header className="mb-10 text-center">
          <Badge variant="outline" className="mb-4 font-mono text-[10px]">
            第 {chapter.chapter_num} 章
          </Badge>
          <h1 className="font-serif text-3xl md:text-4xl font-bold leading-tight">
            {chapter.title || "(无标题)"}
          </h1>
          <div className="flex items-center justify-center gap-3 mt-4 text-xs text-muted-foreground">
            {chapter.pov && (
              <span className="flex items-center gap-1">
                <Eye className="size-3" />
                {chapter.pov}
              </span>
            )}
            <span className="tabular-nums">{chapter.word_count.toLocaleString()} 字</span>
            {chapter.consistency_warnings?.length > 0 && (
              <Badge variant="destructive" className="text-[9px]">
                <AlertTriangle className="size-2.5 mr-0.5" />
                {chapter.consistency_warnings.length} 警告
              </Badge>
            )}
          </div>
        </header>

        {/* Warnings */}
        {chapter.consistency_warnings?.length > 0 && (
          <Card className="p-4 mb-8 border-lymo-vermilion-500/30 bg-lymo-vermilion-500/5">
            <div className="flex items-start gap-2">
              <AlertTriangle className="size-4 text-lymo-vermilion-400 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-lymo-vermilion-300 mb-1">
                  一致性警告
                </div>
                <ul className="text-xs text-muted-foreground space-y-1">
                  {chapter.consistency_warnings.map((w, i) => (
                    <li key={i}>· {w}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        )}

        {/* Prose */}
        <div
          className="text-base leading-9 text-foreground space-y-5"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          {chapter.content.split("\n").filter((p) => p.trim()).map((p, i) => {
            if (p.trim() === "***") {
              return (
                <div key={i} className="flex items-center justify-center py-4">
                  <span className="text-lymo-gold-500 tracking-widest text-xs">✦ ✦ ✦</span>
                </div>
              );
            }
            return (
              <p key={i} className="indent-8 text-justify">
                {p}
              </p>
            );
          })}
        </div>

        {/* Footer nav */}
        <div className="mt-16 pt-8 border-t border-border/40 flex items-center justify-between">
          {chapterNum > 1 ? (
            <Link href={`/stories/${storyId}/chapters/${chapterNum - 1}`}>
              <Button variant="outline" size="sm">
                <ArrowLeft className="size-3.5" />
                上一章
              </Button>
            </Link>
          ) : (
            <span />
          )}
          <Link href={`/stories/${storyId}/chapters/${chapterNum + 1}`}>
            <Button variant="outline" size="sm">
              下一章
              <ArrowRight className="size-3.5" />
            </Button>
          </Link>
        </div>
      </motion.article>
    </div>
  );
}

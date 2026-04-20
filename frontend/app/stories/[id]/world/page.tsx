"use client";

import { use, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "motion/react";
import {
  Globe,
  Sparkles,
  Shield,
  TrendingUp,
  Scroll,
  Compass,
} from "lucide-react";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getStoryBible } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const STANCE_COLORS: Record<string, string> = {
  hostile: "#c73e3a",
  neutral: "#a8b3bd",
  allied: "#5aa67d",
};

const STANCE_LABEL: Record<string, string> = {
  hostile: "敌对",
  neutral: "中立",
  allied: "友好",
};

export default function WorldPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: storyId } = use(params);
  const [bible, setBible] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const b = await getStoryBible(storyId);
        setBible(b);
      } finally {
        setLoading(false);
      }
    })();
  }, [storyId]);

  const world = bible?.world || {};
  const factions = world.factions || [];
  const powerSystem = world.power_system || bible?.power_system;
  const specialAbility = world.special_ability;
  const worldRules = bible?.world_rules || world.world_rules || [];

  // Faction radial layout via ECharts graph
  const factionOption = useMemo(() => {
    if (!factions.length) return null;
    const nodes = [
      {
        id: "protagonist",
        name: "主角",
        symbolSize: 40,
        itemStyle: { color: "#d4a84b" },
        label: { color: "#fff", fontWeight: 700 },
        category: 0,
      },
      ...factions.map((f: any, i: number) => ({
        id: `faction_${i}`,
        name: f.name,
        symbolSize: 30,
        itemStyle: { color: STANCE_COLORS[f.stance] || "#a8b3bd" },
        label: { color: "#e8ecef" },
        category: ["allied", "neutral", "hostile"].indexOf(f.stance) + 1,
        tooltip: { formatter: () => `<b>${f.name}</b><br/>${f.description || ""}` },
      })),
    ];
    const links = factions.map((f: any, i: number) => ({
      source: "protagonist",
      target: `faction_${i}`,
      lineStyle: {
        color: STANCE_COLORS[f.stance] || "#a8b3bd",
        width: 2,
        opacity: 0.6,
        type: f.stance === "hostile" ? "dashed" : "solid",
      },
      label: { show: false },
    }));
    return {
      backgroundColor: "transparent",
      tooltip: {
        backgroundColor: "#1d252f",
        borderColor: "#2d3d4e",
        textStyle: { color: "#e8ecef", fontSize: 12 },
      },
      legend: [
        {
          bottom: 10,
          left: "center",
          textStyle: { color: "#a8b3bd" },
          data: [
            { name: "主角", icon: "circle" },
            { name: "友好", icon: "circle" },
            { name: "中立", icon: "circle" },
            { name: "敌对", icon: "circle" },
          ],
        },
      ],
      series: [
        {
          type: "graph",
          layout: "circular",
          symbol: "circle",
          circular: { rotateLabel: false },
          roam: true,
          label: { show: true, position: "bottom", fontSize: 12 },
          categories: [
            { name: "主角" },
            { name: "友好" },
            { name: "中立" },
            { name: "敌对" },
          ],
          data: nodes,
          links,
          lineStyle: { curveness: 0.2 },
          emphasis: {
            focus: "adjacency",
            lineStyle: { width: 4 },
          },
        },
      ],
    };
  }, [factions]);

  if (loading || !bible) {
    return (
      <div className="px-8 py-6 max-w-7xl mx-auto space-y-6">
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="px-8 py-6 max-w-7xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-serif text-3xl font-bold flex items-center gap-3 mb-2">
          <Globe className="size-7 text-lymo-stellar-400" />
          世界观
        </h1>
        <p className="text-sm text-muted-foreground">
          {bible.genre || "未分类题材"} · {factions.length} 个势力 · {worldRules.length} 条世界规则
        </p>
      </motion.div>

      {/* World background */}
      {world.world_background && (
        <Card className="p-6">
          <h3 className="font-serif font-bold text-lg mb-3 flex items-center gap-2">
            <Compass className="size-5 text-lymo-gold-400" />
            世界背景
          </h3>
          <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
            {world.world_background}
          </p>
        </Card>
      )}

      {/* Special ability (金手指) */}
      {specialAbility?.name && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Card className="p-6 relative overflow-hidden border-lymo-gold-500/40">
            <div className="absolute -top-20 -right-20 w-60 h-60 rounded-full bg-lymo-gold-500/10 blur-3xl" />
            <div className="relative">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="size-5 text-lymo-gold-400" />
                <Badge variant="gold">金手指</Badge>
              </div>
              <h2 className="font-serif text-3xl font-bold text-gold-grad mb-3">
                {specialAbility.name}
              </h2>
              <p className="text-sm leading-relaxed text-muted-foreground mb-4">
                {specialAbility.description}
              </p>
              {specialAbility.functions?.length > 0 && (
                <div>
                  <div className="text-[10px] tracking-wider text-lymo-gold-400 font-semibold uppercase mb-2">
                    能力列表
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {specialAbility.functions.map((f: string, i: number) => (
                      <Badge key={i} variant="gold" className="font-serif">
                        {f}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </motion.div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Faction graph */}
        {factionOption && (
          <Card className="p-6">
            <h3 className="font-serif font-bold text-lg mb-3 flex items-center gap-2">
              <Shield className="size-5 text-lymo-vermilion-400" />
              势力分布
            </h3>
            <div className="h-[420px]">
              <ReactECharts option={factionOption} style={{ height: "100%", width: "100%" }} />
            </div>
          </Card>
        )}

        {/* Faction list */}
        <Card className="p-6">
          <h3 className="font-serif font-bold text-lg mb-3 flex items-center gap-2">
            <Shield className="size-5 text-lymo-stellar-400" />
            势力详情
          </h3>
          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
            {factions.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                暂无势力设定
              </p>
            ) : (
              factions.map((f: any, i: number) => (
                <div
                  key={i}
                  className="p-4 rounded-md bg-secondary/30 border border-border/40 relative overflow-hidden"
                >
                  <div
                    className="absolute left-0 top-0 bottom-0 w-1"
                    style={{ background: STANCE_COLORS[f.stance] || "#a8b3bd" }}
                  />
                  <div className="flex items-center justify-between mb-2 pl-2">
                    <h4 className="font-serif font-bold">{f.name}</h4>
                    <Badge
                      variant={
                        f.stance === "hostile"
                          ? "vermilion"
                          : f.stance === "allied"
                          ? "jade"
                          : "ghost"
                      }
                      className="text-[9px]"
                    >
                      {STANCE_LABEL[f.stance] || f.stance}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground pl-2">
                    {f.description}
                  </p>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Power system */}
      {powerSystem?.name && (
        <Card className="p-6">
          <h3 className="font-serif font-bold text-lg mb-4 flex items-center gap-2">
            <TrendingUp className="size-5 text-lymo-vermilion-400" />
            力量体系 · {powerSystem.name}
          </h3>
          {powerSystem.levels?.length > 0 && (
            <div className="mb-5">
              <div className="text-[10px] tracking-wider text-muted-foreground font-semibold uppercase mb-3">
                境界阶梯（从低到高）
              </div>
              <div className="flex items-end gap-1 overflow-x-auto pb-2">
                {powerSystem.levels.map((lv: string, i: number) => {
                  const h = 30 + (i / Math.max(1, powerSystem.levels.length - 1)) * 60;
                  return (
                    <div key={i} className="flex flex-col items-center gap-1 min-w-[72px]">
                      <div
                        className="w-full rounded-t-md bg-gradient-to-t from-lymo-vermilion-600 to-lymo-gold-500 transition-all hover:brightness-125"
                        style={{ height: `${h}px`, opacity: 0.35 + (i / powerSystem.levels.length) * 0.55 }}
                      />
                      <span className="text-[11px] font-serif text-center whitespace-nowrap">
                        {lv}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {powerSystem.rules?.length > 0 && (
            <div>
              <div className="text-[10px] tracking-wider text-muted-foreground font-semibold uppercase mb-2">
                体系规则
              </div>
              <ul className="space-y-1.5">
                {powerSystem.rules.map((r: string, i: number) => (
                  <li
                    key={i}
                    className="text-sm flex gap-2 text-muted-foreground"
                  >
                    <span className="text-lymo-vermilion-400 shrink-0">·</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}

      {/* World rules */}
      {worldRules.length > 0 && (
        <Card className="p-6">
          <h3 className="font-serif font-bold text-lg mb-4 flex items-center gap-2">
            <Scroll className="size-5 text-lymo-jade-400" />
            世界规则（{worldRules.length}）
          </h3>
          <div className="grid md:grid-cols-2 gap-3">
            {worldRules.map((r: any, i: number) => (
              <div
                key={i}
                className="p-3 rounded-md bg-secondary/30 border border-border/40 relative"
              >
                <Badge variant="outline" className="mb-2 text-[10px]">
                  {r.rule_id}
                </Badge>
                <p className="text-sm">{r.description}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

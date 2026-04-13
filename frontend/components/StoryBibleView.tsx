"use client";

import { useState } from "react";
import type { StoryBible } from "@/types";

interface Props {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  bible: any;
}

export default function StoryBibleView({ bible }: Props) {
  const [open, setOpen] = useState(false);

  const isV2 = bible.bible_version === 2;
  const world = bible.world;
  const protagonist = bible.protagonist;
  const antagonist = bible.antagonist;
  const supportingChars = bible.supporting_characters || [];
  const volumes = bible.volumes || [];
  const specialAbility = world?.special_ability;
  const factions = world?.factions || [];

  return (
    <div className="border rounded-lg">
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-4 text-left font-medium flex justify-between items-center hover:bg-gray-50"
      >
        <span>故事圣经：《{bible.title}》</span>
        <span className="text-gray-400">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="p-4 border-t space-y-4 text-sm">
          {/* Basic info */}
          <div>
            <h4 className="font-medium mb-1">基本信息</h4>
            <p>类型：{bible.genre} | 基调：{bible.tone || bible.style_guide?.tone}</p>
            {bible.one_line_summary && (
              <p className="mt-1 text-gray-700 font-medium">{bible.one_line_summary}</p>
            )}
            <p className="mt-1">背景：{isV2 && world ? world.world_background : bible.setting}</p>
          </div>

          {/* Synopsis (V2) */}
          {bible.synopsis && (
            <div>
              <h4 className="font-medium mb-1">故事梗概</h4>
              <p className="text-gray-700">{bible.synopsis}</p>
            </div>
          )}

          {/* Special ability (V2) */}
          {specialAbility && specialAbility.name && (
            <div>
              <h4 className="font-medium mb-1">🔥 金手指：{specialAbility.name}</h4>
              <p className="text-gray-600">{specialAbility.description}</p>
              {specialAbility.functions?.length ? (
                <ul className="list-disc pl-5 mt-1 space-y-0.5">
                  {specialAbility.functions.map((f: string, i: number) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          )}

          {/* Factions (V2) */}
          {factions.length > 0 && (
            <div>
              <h4 className="font-medium mb-1">势力</h4>
              <div className="grid gap-2">
                {factions.map((f: any, i: number) => (
                  <div key={i} className="p-2 bg-gray-50 rounded flex items-start gap-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      f.stance === "hostile" ? "bg-red-100 text-red-700"
                        : f.stance === "allied" ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-600"
                    }`}>{f.stance || "中立"}</span>
                    <div>
                      <p className="font-medium">{f.name}</p>
                      <p className="text-gray-600">{f.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* World rules */}
          {bible.world_rules?.length > 0 && (
            <div>
              <h4 className="font-medium mb-1">世界规则</h4>
              <ul className="list-disc pl-5 space-y-1">
                {bible.world_rules.map((r: any) => (
                  <li key={r.rule_id}>{r.description}</li>
                ))}
              </ul>
            </div>
          )}

          {bible.power_system && (
            <div>
              <h4 className="font-medium mb-1">力量体系：{bible.power_system.name}</h4>
              <p>等级：{bible.power_system.levels?.join(" → ")}</p>
            </div>
          )}

          {/* Characters — V2 detailed or V1 simple */}
          {isV2 && protagonist ? (
            <div>
              <h4 className="font-medium mb-2">角色</h4>
              <div className="space-y-3">
                {[protagonist, antagonist, ...supportingChars].filter(Boolean).map((c: any, i: number) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium">{c!.name}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        c!.role === "protagonist" ? "bg-amber-100 text-amber-700"
                          : c!.role === "antagonist" ? "bg-red-100 text-red-700"
                            : "bg-gray-100 text-gray-600"
                      }`}>{c!.role}</span>
                      {c!.gender && <span className="text-xs text-gray-400">{c!.gender} · {c!.age}</span>}
                    </div>
                    {c!.appearance && <p className="text-gray-500 text-xs mb-1">外貌：{c!.appearance}</p>}
                    <p className="text-gray-700">{c!.personality}</p>
                    {c!.background && <p className="text-gray-600 mt-1">{c!.background}</p>}
                    {c!.weaknesses?.length ? (
                      <p className="text-xs text-red-500 mt-1">弱点：{c!.weaknesses.join("、")}</p>
                    ) : null}
                    {c!.arc_plan && <p className="text-xs text-blue-600 mt-1">弧线：{c!.arc_plan}</p>}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <h4 className="font-medium mb-1">角色（{bible.characters?.length || 0}）</h4>
              <div className="grid gap-2">
                {bible.characters?.map((c: any) => (
                  <div key={c.character_id} className="p-2 bg-gray-50 rounded">
                    <p className="font-medium">{c.name}（{c.role}）</p>
                    <p className="text-gray-600">{c.personality}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Volumes (V2) or Long Outline (V1) */}
          {volumes.length > 0 ? (
            <div>
              <h4 className="font-medium mb-2">分卷大纲（{volumes.length} 卷）</h4>
              <div className="space-y-4">
                {volumes.map((vol: any, i: number) => (
                  <div key={i} className="border-l-4 border-amber-400 pl-3">
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="font-medium text-amber-700">{vol.volume_name || `第${(vol.volume_num) || i+1}卷`}</span>
                      <span className="text-xs text-gray-500">
                        第 {vol.chapter_start}-{vol.chapter_end} 章
                      </span>
                    </div>
                    <p className="text-gray-700 mb-2">{vol.main_plot}</p>
                    {(vol.subplots)?.length > 0 && (
                      <details className="mb-1">
                        <summary className="text-xs text-gray-500 cursor-pointer">支线（{(vol.subplots).length}）</summary>
                        <ol className="list-decimal pl-5 text-xs text-gray-600 mt-1 space-y-0.5">
                          {vol.subplots.map((s: string, j: number) => <li key={j}>{s}</li>)}
                        </ol>
                      </details>
                    )}
                    {(vol.conflicts)?.length > 0 && (
                      <details>
                        <summary className="text-xs text-gray-500 cursor-pointer">冲突（{(vol.conflicts).length}）</summary>
                        <ul className="list-disc pl-5 text-xs text-red-500 mt-1 space-y-0.5">
                          {vol.conflicts.map((c: string, j: number) => <li key={j}>{c}</li>)}
                        </ul>
                      </details>
                    )}
                    {vol.climax_event && (
                      <p className="text-xs text-amber-600 mt-1">⚡ 高潮：{vol.climax_event}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : bible.long_outline && bible.long_outline.arcs?.length > 0 ? (
            <div>
              <h4 className="font-medium mb-2">长线大纲（预计 {bible.long_outline.target_chapters} 章）</h4>
              <ol className="space-y-3">
                {bible.long_outline.arcs.map((arc: any, i: number) => (
                  <li key={i} className="relative pl-6">
                    <div className="absolute left-0 top-1.5 w-3 h-3 rounded-full bg-amber-500" />
                    {i < bible.long_outline!.arcs.length - 1 && (
                      <div className="absolute left-[5px] top-5 bottom-[-12px] w-px bg-amber-200" />
                    )}
                    <div className="flex items-baseline gap-2">
                      <span className="font-medium text-amber-700">{arc.name}</span>
                      <span className="text-xs text-gray-500">第 {arc.chapter_start}-{arc.chapter_end} 章</span>
                    </div>
                    <p className="mt-1 text-gray-700">{arc.goal}</p>
                    {arc.key_milestones?.length > 0 && (
                      <ul className="mt-1.5 pl-4 list-disc text-xs text-gray-500 space-y-0.5">
                        {arc.key_milestones.map((m: string, j: number) => <li key={j}>{m}</li>)}
                      </ul>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          ) : null}

          {bible.initial_conflicts?.length > 0 && (
            <div>
              <h4 className="font-medium mb-1">核心冲突</h4>
              <ul className="list-disc pl-5">
                {bible.initial_conflicts.map((c: any, i: number) => (
                  <li key={i}>{typeof c === "string" ? c : JSON.stringify(c)}</li>
                ))}
              </ul>
            </div>
          )}

          {bible.planned_arc && (
            <div>
              <h4 className="font-medium mb-1">故事弧线</h4>
              <p>{bible.planned_arc}</p>
            </div>
          )}

          {/* Inspiration (V2) */}
          {bible.inspiration && (
            <details>
              <summary className="font-medium cursor-pointer">作品灵感</summary>
              <p className="mt-2 text-gray-700 whitespace-pre-line">{bible.inspiration}</p>
            </details>
          )}

          {bible.taboos?.length > 0 && (
            <div>
              <h4 className="font-medium mb-1">禁忌</h4>
              <p className="text-red-600">{bible.taboos.map((t: any) => typeof t === "string" ? t : JSON.stringify(t)).join("、")}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

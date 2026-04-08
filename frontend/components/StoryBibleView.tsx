"use client";

import { useState } from "react";
import type { StoryBible } from "@/types";

interface Props {
  bible: StoryBible;
}

export default function StoryBibleView({ bible }: Props) {
  const [open, setOpen] = useState(false);

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
          <div>
            <h4 className="font-medium mb-1">基本信息</h4>
            <p>类型：{bible.genre} | 基调：{bible.style_guide?.tone}</p>
            <p>背景：{bible.setting}</p>
          </div>

          {bible.world_rules?.length > 0 && (
            <div>
              <h4 className="font-medium mb-1">世界规则</h4>
              <ul className="list-disc pl-5 space-y-1">
                {bible.world_rules.map((r) => (
                  <li key={r.rule_id}>{r.description}</li>
                ))}
              </ul>
            </div>
          )}

          {bible.power_system && (
            <div>
              <h4 className="font-medium mb-1">
                力量体系：{bible.power_system.name}
              </h4>
              <p>等级：{bible.power_system.levels?.join(" → ")}</p>
            </div>
          )}

          <div>
            <h4 className="font-medium mb-1">
              角色（{bible.characters?.length || 0}）
            </h4>
            <div className="grid gap-2">
              {bible.characters?.map((c) => (
                <div key={c.character_id} className="p-2 bg-gray-50 rounded">
                  <p className="font-medium">
                    {c.name}（{c.role}）
                  </p>
                  <p className="text-gray-600">{c.personality}</p>
                </div>
              ))}
            </div>
          </div>

          {bible.initial_conflicts?.length > 0 && (
            <div>
              <h4 className="font-medium mb-1">初始冲突</h4>
              <ul className="list-disc pl-5">
                {bible.initial_conflicts.map((c, i) => (
                  <li key={i}>{typeof c === "string" ? c : (c as { description?: string }).description || JSON.stringify(c)}</li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h4 className="font-medium mb-1">故事弧线</h4>
            <p>{bible.planned_arc}</p>
          </div>

          {bible.taboos?.length > 0 && (
            <div>
              <h4 className="font-medium mb-1">禁忌</h4>
              <p className="text-red-600">{bible.taboos.map((t) => typeof t === "string" ? t : (t as { description?: string }).description || JSON.stringify(t)).join("、")}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

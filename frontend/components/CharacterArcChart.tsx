"use client";

import { useEffect, useState } from "react";
import { getCharacters, getCharacterArcHistory } from "@/lib/api";

interface Props {
  storyId: string;
}

export default function CharacterArcChart({ storyId }: Props) {
  const [characters, setCharacters] = useState<any[]>([]);
  const [selectedChar, setSelectedChar] = useState<string>("");
  const [arcData, setArcData] = useState<{ arcs: any[]; states: any[] } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCharacters(storyId).then((chars) => {
      setCharacters(chars);
      const protag = chars.find((c: any) => c.role === "protagonist");
      if (protag) setSelectedChar(protag.character_id);
    }).catch(console.error);
  }, [storyId]);

  useEffect(() => {
    if (!selectedChar) return;
    setLoading(true);
    getCharacterArcHistory(storyId, selectedChar)
      .then(setArcData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [storyId, selectedChar]);

  return (
    <div>
      {/* Character selector */}
      <div className="flex items-center gap-3 mb-4">
        <label className="text-sm text-gray-600">角色：</label>
        <select
          value={selectedChar}
          onChange={(e) => setSelectedChar(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        >
          {characters.map((c: any) => (
            <option key={c.character_id} value={c.character_id}>
              {c.name}（{c.role}）
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="text-gray-400 text-sm">加载中...</p>}

      {arcData && !loading && (
        <div className="space-y-4">
          {/* Per-chapter emotional states */}
          {arcData.states.length > 0 ? (
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">逐章心境变化</h4>
              <div className="space-y-0">
                {arcData.states.map((s: any, i: number) => (
                  <div key={i} className="flex gap-3 relative">
                    <div className="flex flex-col items-center w-10 flex-shrink-0">
                      <div className="w-3 h-3 rounded-full bg-blue-500 z-10" />
                      {i < arcData.states.length - 1 && (
                        <div className="w-px flex-1 bg-blue-200 min-h-[30px]" />
                      )}
                    </div>
                    <div className="pb-4 flex-1 min-w-0">
                      <div className="flex items-baseline gap-2">
                        <span className="text-xs font-medium text-gray-500">第{s.chapter_num}章</span>
                        <span className="text-xs text-gray-400">{s.status}</span>
                      </div>
                      {s.emotional_state && (
                        <p className="text-sm text-gray-700 mt-0.5">{s.emotional_state}</p>
                      )}
                      {s.goals_update && (
                        <p className="text-xs text-blue-600 mt-0.5">目标变化：{s.goals_update}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">暂无逐章状态数据（需要生成章节后自动提取）</p>
          )}

          {/* Arc summaries */}
          {arcData.arcs.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">阶段性弧线总结</h4>
              <div className="space-y-3">
                {arcData.arcs.map((a: any, i: number) => (
                  <div key={i} className="border-l-4 border-amber-400 pl-3 py-2">
                    <div className="flex items-baseline gap-2">
                      <span className="font-medium text-amber-700 text-sm">{a.arc_name}</span>
                      <span className="text-xs text-gray-400">第{a.chapter_num}章触发</span>
                    </div>
                    {a.summary?.current_phase && (
                      <p className="text-sm text-gray-700 mt-1">{a.summary.current_phase}</p>
                    )}
                    {a.summary?.emotional_trajectory && (
                      <p className="text-xs text-gray-500 mt-0.5">情绪：{a.summary.emotional_trajectory}</p>
                    )}
                    {a.summary?.motivation_now && (
                      <p className="text-xs text-blue-600 mt-0.5">动机：{a.summary.motivation_now}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {arcData.arcs.length === 0 && arcData.states.length === 0 && (
            <p className="text-gray-400 text-sm text-center py-8">暂无角色弧线数据</p>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import type { StoryEvent } from "@/types";

function getVisibilityInfo(vis: StoryEvent["visibility"]): {
  color: string;
  bg: string;
  label: string;
} {
  if (typeof vis === "string") {
    if (vis === "full") return { color: "text-green-700", bg: "bg-green-100", label: "公开" };
    if (vis === "hidden") return { color: "text-gray-500", bg: "bg-gray-100", label: "隐藏" };
    return { color: "text-amber-700", bg: "bg-amber-100", label: "部分" };
  }
  if (vis?.public) return { color: "text-green-700", bg: "bg-green-100", label: "公开" };
  if ((vis?.known_to?.length ?? 0) > 0) {
    return { color: "text-amber-700", bg: "bg-amber-100", label: `仅 ${vis.known_to.join(", ")}` };
  }
  return { color: "text-gray-500", bg: "bg-gray-100", label: "隐藏" };
}

export default function EventTimeline({ events }: { events: StoryEvent[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (events.length === 0) {
    return <p className="text-gray-500 text-sm py-8 text-center">暂无事件数据</p>;
  }

  // Group events by time
  const timeGroups = new Map<number, StoryEvent[]>();
  const sorted = [...events].sort((a, b) => (a.time ?? 0) - (b.time ?? 0));
  for (const ev of sorted) {
    const t = ev.time ?? 0;
    if (!timeGroups.has(t)) timeGroups.set(t, []);
    timeGroups.get(t)!.push(ev);
  }

  const entries = [...timeGroups.entries()];

  return (
    <div className="space-y-0">
      {/* Legend */}
      <div className="flex gap-4 mb-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" /> 公开
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" /> 部分可见
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-gray-400 inline-block" /> 隐藏
        </span>
      </div>

      {entries.map(([time, group], gi) => (
        <div key={time} className="relative flex gap-4">
          {/* Timeline spine */}
          <div className="flex flex-col items-center w-16 flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center z-10">
              T{time}
            </div>
            {gi < entries.length - 1 && (
              <div className="w-px flex-1 bg-blue-200 min-h-[40px]" />
            )}
          </div>

          {/* Events at this time */}
          <div className="flex-1 pb-6 space-y-2">
            {group.map((ev) => {
              const vis = getVisibilityInfo(ev.visibility);
              const isExpanded = expandedId === ev.event_id;
              const hasCausal = ev.pre_events && ev.pre_events.length > 0;

              return (
                <div
                  key={ev.event_id}
                  className="border rounded-lg p-3 hover:shadow-sm transition cursor-pointer bg-white"
                  onClick={() => setExpandedId(isExpanded ? null : ev.event_id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs text-gray-400">
                          {ev.event_id}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${vis.bg} ${vis.color}`}>
                          {vis.label}
                        </span>
                        {ev.location && (
                          <span className="text-[10px] text-gray-400">
                            📍 {ev.location}
                          </span>
                        )}
                        {hasCausal && (
                          <span className="text-[10px] text-gray-400">
                            ← {ev.pre_events.join(", ")}
                          </span>
                        )}
                      </div>
                      <p className="text-sm mt-1 text-gray-800">{ev.description}</p>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t text-xs text-gray-500 space-y-1">
                      {ev.actors?.length > 0 && (
                        <p>参与角色：{ev.actors.join(", ")}</p>
                      )}
                      {ev.effects?.length > 0 && (
                        <p>影响：{ev.effects.join("; ")}</p>
                      )}
                      {ev.pre_events?.length > 0 && (
                        <p>前置事件：{ev.pre_events.join(", ")}</p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

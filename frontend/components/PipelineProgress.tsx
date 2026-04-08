"use client";

import type { GenerationProgressData } from "@/lib/api";

interface Props {
  progress: GenerationProgressData | null;
}

const STATUS_STYLES: Record<string, { dot: string; text: string; bg: string }> = {
  pending: { dot: "bg-gray-300", text: "text-gray-400", bg: "" },
  running: { dot: "bg-blue-500 animate-pulse", text: "text-blue-700", bg: "bg-blue-50" },
  done: { dot: "bg-green-500", text: "text-green-700", bg: "bg-green-50" },
  error: { dot: "bg-red-500", text: "text-red-700", bg: "bg-red-50" },
};

export default function PipelineProgress({ progress }: Props) {
  if (!progress || progress.stages.length === 0) return null;

  return (
    <div className="border rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-sm">
          第{progress.chapter_num}章生成中
        </h3>
        <span className="text-xs text-gray-400">
          已用时 {progress.elapsed_seconds}s
        </span>
      </div>

      <div className="space-y-2">
        {progress.stages.map((stage, i) => {
          const style = STATUS_STYLES[stage.status] || STATUS_STYLES.pending;
          return (
            <div
              key={stage.name}
              className={`flex items-center gap-3 p-2 rounded-lg transition-all ${style.bg}`}
            >
              {/* Step number */}
              <span className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-100 text-xs font-medium text-gray-500">
                {i + 1}
              </span>

              {/* Status dot */}
              <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${style.dot}`} />

              {/* Label */}
              <span className={`text-sm font-medium w-28 ${style.text}`}>
                {stage.label}
              </span>

              {/* Detail */}
              <span className="text-xs text-gray-500 flex-1 truncate">
                {stage.status === "running" ? (
                  <span className="inline-flex items-center gap-1">
                    <span className="animate-pulse">{stage.detail || "处理中..."}</span>
                  </span>
                ) : (
                  stage.detail
                )}
              </span>

              {/* Duration */}
              {stage.duration_ms > 0 && (
                <span className="text-xs text-gray-400 w-14 text-right">
                  {(stage.duration_ms / 1000).toFixed(1)}s
                </span>
              )}
            </div>
          );
        })}
      </div>

      {progress.error && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
          {progress.error}
        </div>
      )}
    </div>
  );
}

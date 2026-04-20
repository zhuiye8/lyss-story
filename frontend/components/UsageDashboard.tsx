"use client";

import type { UsageResponse } from "@/lib/admin-api";
import { agentLabel } from "@/lib/agent-labels";

interface Props {
  usage: UsageResponse | null;
}

export default function UsageDashboard({ usage }: Props) {
  if (!usage) return <p className="text-gray-400">加载中...</p>;

  const total = usage.total;
  const maxTokens = Math.max(...usage.stats.map((s) => s.total_tokens || 0), 1);

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">用量统计（近7天）</h3>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg text-center">
          <p className="text-2xl font-bold text-blue-700">{total.total_calls || 0}</p>
          <p className="text-xs text-gray-500">总调用次数</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg text-center">
          <p className="text-2xl font-bold text-green-700">{((total.total_tokens || 0) / 1000).toFixed(1)}K</p>
          <p className="text-xs text-gray-500">总Token数</p>
        </div>
        <div className="p-4 bg-amber-50 rounded-lg text-center">
          <p className="text-2xl font-bold text-amber-700">{(total.total_cost || 0).toFixed(4)}</p>
          <p className="text-xs text-gray-500">总成本（混合币种）</p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg text-center">
          <p className="text-2xl font-bold text-purple-700">{((total.avg_latency_ms || 0) / 1000).toFixed(1)}s</p>
          <p className="text-xs text-gray-500">平均延迟</p>
        </div>
      </div>

      {/* Per-agent bar chart (simple CSS bars) */}
      <div className="space-y-3">
        {usage.stats.map((s) => (
          <div key={s.group_key} className="flex items-center gap-3">
            <span className="w-44 text-sm font-medium text-right truncate" title={s.group_key}>{agentLabel(s.group_key)}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-6 relative">
              <div
                className="bg-blue-500 h-6 rounded-full flex items-center justify-end pr-2"
                style={{ width: `${Math.max((s.total_tokens / maxTokens) * 100, 5)}%` }}
              >
                <span className="text-xs text-white font-medium">
                  {(s.total_tokens / 1000).toFixed(1)}K
                </span>
              </div>
            </div>
            <span className="w-20 text-xs text-gray-500 text-right">
              {s.total_calls}次 / {s.total_cost.toFixed(3)}
            </span>
          </div>
        ))}
        {usage.stats.length === 0 && (
          <p className="text-gray-400 text-center py-4">暂无调用数据</p>
        )}
      </div>
    </div>
  );
}

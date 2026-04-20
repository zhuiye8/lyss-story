"use client";

import { useEffect, useState } from "react";
import { getUsage, type UsageResponse } from "@/lib/admin-api";
import { agentLabel } from "@/lib/agent-labels";

const AGENT_COLORS: Record<string, string> = {
  concept: "#f59e0b",
  world_builder: "#10b981",
  character_designer: "#6366f1",
  outline_planner: "#ec4899",
  world: "#14b8a6",
  planner: "#8b5cf6",
  camera: "#06b6d4",
  writer: "#ef4444",
  consistency: "#f97316",
  titler: "#84cc16",
  character_arc: "#a855f7",
  extractor: "#64748b",
  outline_parser: "#0ea5e9",
};

export default function LLMCostDashboard() {
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [groupBy, setGroupBy] = useState("agent");
  const [days, setDays] = useState(7);

  useEffect(() => {
    getUsage(groupBy, days).then(setUsage).catch(console.error);
  }, [groupBy, days]);

  if (!usage) {
    return <p className="text-gray-400 text-sm text-center py-8">加载中...</p>;
  }

  const { stats, total } = usage;
  const maxTokens = Math.max(...stats.map((s) => s.total_tokens), 1);

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-4">
        <select
          value={groupBy}
          onChange={(e) => setGroupBy(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="agent">按 Agent</option>
          <option value="story">按故事</option>
          <option value="model">按模型</option>
        </select>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value={1}>最近 1 天</option>
          <option value={7}>最近 7 天</option>
          <option value={30}>最近 30 天</option>
        </select>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-3">
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-xl font-bold text-blue-600">{total.total_calls}</p>
          <p className="text-xs text-gray-500">总调用</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-xl font-bold text-green-600">
            {total.total_tokens > 1000000
              ? `${(total.total_tokens / 1000000).toFixed(1)}M`
              : total.total_tokens > 1000
                ? `${(total.total_tokens / 1000).toFixed(0)}K`
                : total.total_tokens}
          </p>
          <p className="text-xs text-gray-500">总 Token</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-xl font-bold text-amber-600">
            ¥{total.total_cost.toFixed(2)}
          </p>
          <p className="text-xs text-gray-500">总成本</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-xl font-bold text-purple-600">
            {total.avg_latency_ms > 1000
              ? `${(total.avg_latency_ms / 1000).toFixed(1)}s`
              : `${Math.round(total.avg_latency_ms)}ms`}
          </p>
          <p className="text-xs text-gray-500">平均延迟</p>
        </div>
      </div>

      {/* Token distribution bar chart */}
      {stats.length > 0 ? (
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-3">Token 分布</h4>
          <div className="space-y-2">
            {stats.sort((a, b) => b.total_tokens - a.total_tokens).map((s) => {
              const pct = (s.total_tokens / maxTokens) * 100;
              const color = AGENT_COLORS[s.group_key] || "#6b7280";
              return (
                <div key={s.group_key} className="flex items-center gap-3 text-sm">
                  <span className="w-44 text-right text-gray-600 truncate" title={s.group_key}>
                    {agentLabel(s.group_key)}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${pct}%`, backgroundColor: color }}
                    />
                  </div>
                  <span className="w-20 text-xs text-gray-500 text-right">
                    {s.total_tokens > 1000 ? `${(s.total_tokens / 1000).toFixed(0)}K` : s.total_tokens}
                  </span>
                  <span className="w-16 text-xs text-gray-400 text-right">
                    ¥{s.total_cost.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <p className="text-gray-400 text-sm text-center py-4">暂无调用数据</p>
      )}

      {/* Detail table */}
      {stats.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-3">详细数据</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b text-gray-500">
                  <th className="text-left py-2 px-2">{groupBy === "agent" ? "Agent" : groupBy === "story" ? "Story" : "Model"}</th>
                  <th className="text-right py-2 px-2">调用</th>
                  <th className="text-right py-2 px-2">输入 Token</th>
                  <th className="text-right py-2 px-2">输出 Token</th>
                  <th className="text-right py-2 px-2">成本</th>
                  <th className="text-right py-2 px-2">平均延迟</th>
                </tr>
              </thead>
              <tbody>
                {stats.map((s) => (
                  <tr key={s.group_key} className="border-b hover:bg-gray-50">
                    <td className="py-1.5 px-2 font-medium" title={s.group_key}>{agentLabel(s.group_key)}</td>
                    <td className="text-right py-1.5 px-2">{s.total_calls}</td>
                    <td className="text-right py-1.5 px-2">{s.total_input_tokens.toLocaleString()}</td>
                    <td className="text-right py-1.5 px-2">{s.total_output_tokens.toLocaleString()}</td>
                    <td className="text-right py-1.5 px-2">¥{s.total_cost.toFixed(3)}</td>
                    <td className="text-right py-1.5 px-2">{Math.round(s.avg_latency_ms)}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

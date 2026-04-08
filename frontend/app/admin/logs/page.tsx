"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getLogs, getLogDetail, type LLMLogEntry, type LLMLogDetail } from "@/lib/admin-api";

const AGENT_LABELS: Record<string, string> = {
  director: "导演",
  world: "世界引擎",
  planner: "剧情规划",
  camera: "摄影决策",
  writer: "写作",
  consistency: "一致性检查",
};

export default function LogsPage() {
  const [logs, setLogs] = useState<LLMLogEntry[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [detail, setDetail] = useState<LLMLogDetail | null>(null);

  useEffect(() => {
    getLogs({ agent_name: filter || undefined, limit: 100 })
      .then(setLogs)
      .catch(console.error);
  }, [filter]);

  const handleViewDetail = async (logId: number) => {
    if (detail?.id === logId) {
      setDetail(null);
      return;
    }
    const d = await getLogDetail(logId);
    setDetail(d);
  };

  return (
    <main className="max-w-6xl mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">LLM 请求日志</h1>
          <p className="text-gray-500 text-sm">查看每次LLM调用的完整输入/输出</p>
        </div>
        <div className="flex gap-3">
          <Link href="/admin" className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
            管理中心
          </Link>
        </div>
      </div>

      {/* Filter */}
      <div className="mb-4">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="p-2 border rounded text-sm"
        >
          <option value="">全部Agent</option>
          {Object.entries(AGENT_LABELS).map(([key, label]) => (
            <option key={key} value={key}>{label} ({key})</option>
          ))}
        </select>
      </div>

      {/* Log list */}
      <div className="space-y-1">
        {logs.map((log) => (
          <div key={log.id}>
            <button
              onClick={() => handleViewDetail(log.id)}
              className={`w-full text-left p-3 border rounded-lg hover:bg-gray-50 transition text-sm ${
                detail?.id === log.id ? "bg-blue-50 border-blue-300" : ""
              }`}
            >
              <div className="flex items-center gap-4">
                <span className="w-16 text-gray-400 text-xs">
                  #{log.id}
                </span>
                <span className={`w-3 h-3 rounded-full ${log.status === "success" ? "bg-green-500" : "bg-red-500"}`} />
                <span className="w-24 font-medium">
                  {AGENT_LABELS[log.agent_name] || log.agent_name}
                </span>
                <span className="w-32 text-gray-500 text-xs">{log.litellm_model}</span>
                <span className="w-20 text-xs">
                  {log.total_tokens.toLocaleString()} tok
                </span>
                <span className="w-16 text-xs text-gray-400">
                  {(log.latency_ms / 1000).toFixed(1)}s
                </span>
                <span className="w-16 text-xs text-gray-400">
                  ${log.cost_estimate.toFixed(4)}
                </span>
                {log.story_id && (
                  <span className="text-xs text-blue-500">
                    {log.story_id.slice(0, 8)}
                    {log.chapter_num ? `/ch${log.chapter_num}` : ""}
                  </span>
                )}
                <span className="flex-1 text-right text-xs text-gray-400">
                  {new Date(log.created_at).toLocaleString("zh-CN")}
                </span>
              </div>
              {log.error_message && (
                <p className="mt-1 text-xs text-red-600 ml-20">{log.error_message}</p>
              )}
            </button>

            {/* Detail view */}
            {detail?.id === log.id && (
              <div className="ml-4 mr-4 mb-2 p-4 border-l-4 border-blue-400 bg-gray-50 space-y-4">
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 mb-1">System Prompt</h4>
                  <pre className="text-xs bg-white p-3 rounded border max-h-40 overflow-auto whitespace-pre-wrap">
                    {detail.system_prompt}
                  </pre>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 mb-1">User Prompt</h4>
                  <pre className="text-xs bg-white p-3 rounded border max-h-60 overflow-auto whitespace-pre-wrap">
                    {detail.user_prompt}
                  </pre>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 mb-1">Response</h4>
                  <pre className="text-xs bg-white p-3 rounded border max-h-60 overflow-auto whitespace-pre-wrap">
                    {detail.response}
                  </pre>
                </div>
                <div className="text-xs text-gray-400">
                  Input: {detail.input_tokens} | Output: {detail.output_tokens} | Total: {detail.total_tokens} | Cost: ${detail.cost_estimate.toFixed(4)} | Latency: {detail.latency_ms}ms
                </div>
              </div>
            )}
          </div>
        ))}

        {logs.length === 0 && (
          <p className="text-gray-400 text-center py-8">暂无日志记录</p>
        )}
      </div>
    </main>
  );
}

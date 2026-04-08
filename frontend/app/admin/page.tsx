"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import ModelConfigPanel from "@/components/ModelConfigPanel";
import UsageDashboard from "@/components/UsageDashboard";
import {
  listModels, createModel, updateModel, deleteModel,
  getBindings, bindAgent, unbindAgent,
  getUsage,
  type ModelConfig, type AgentBinding, type UsageResponse,
} from "@/lib/admin-api";

const AGENT_LABELS: Record<string, string> = {
  director: "导演",
  world: "世界引擎",
  planner: "剧情规划",
  camera: "摄影决策",
  writer: "写作",
  consistency: "一致性检查",
};

export default function AdminPage() {
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [agents, setAgents] = useState<string[]>([]);
  const [bindings, setBindings] = useState<AgentBinding[]>([]);
  const [usage, setUsage] = useState<UsageResponse | null>(null);

  const refresh = useCallback(async () => {
    const [m, b, u] = await Promise.all([
      listModels(),
      getBindings(),
      getUsage(),
    ]);
    setModels(m);
    setAgents(b.agents);
    setBindings(b.bindings);
    setUsage(u);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleSaveModel = async (model: ModelConfig) => {
    const exists = models.find((m) => m.id === model.id);
    if (exists) {
      await updateModel(model.id, model);
    } else {
      await createModel(model);
    }
    refresh();
  };

  const handleDeleteModel = async (id: string) => {
    if (confirm(`确定删除模型 "${id}"？关联的Agent绑定也会被清除。`)) {
      await deleteModel(id);
      refresh();
    }
  };

  const handleBindAgent = async (agentName: string, modelId: string) => {
    if (modelId === "") {
      await unbindAgent(agentName);
    } else {
      await bindAgent(agentName, modelId);
    }
    refresh();
  };

  const getBindingForAgent = (agentName: string) =>
    bindings.find((b) => b.agent_name === agentName);

  return (
    <main className="max-w-5xl mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">LLM 管理中心</h1>
          <p className="text-gray-500 text-sm">模型配置、Agent绑定、用量监控</p>
        </div>
        <div className="flex gap-3">
          <Link href="/admin/logs" className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
            请求日志
          </Link>
          <Link href="/" className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
            返回首页
          </Link>
        </div>
      </div>

      <div className="space-y-8">
        {/* Model Configuration */}
        <section className="border rounded-lg p-6">
          <ModelConfigPanel
            models={models}
            onSave={handleSaveModel}
            onDelete={handleDeleteModel}
          />
        </section>

        {/* Agent Bindings */}
        <section className="border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Agent — 模型绑定</h3>
          <p className="text-sm text-gray-500 mb-4">
            未绑定的Agent使用环境变量中的默认模型
          </p>
          <div className="space-y-3">
            {agents.map((agent) => {
              const binding = getBindingForAgent(agent);
              return (
                <div key={agent} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                  <span className="w-32 font-medium text-sm">
                    {AGENT_LABELS[agent] || agent}
                  </span>
                  <span className="text-xs text-gray-400 w-24">{agent}</span>
                  <select
                    value={binding?.model_config_id || ""}
                    onChange={(e) => handleBindAgent(agent, e.target.value)}
                    className="flex-1 p-2 border rounded text-sm"
                  >
                    <option value="">默认模型（环境变量）</option>
                    {models.filter((m) => m.is_active).map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.display_name} ({m.litellm_model})
                      </option>
                    ))}
                  </select>
                </div>
              );
            })}
          </div>
        </section>

        {/* Usage Dashboard */}
        <section className="border rounded-lg p-6">
          <UsageDashboard usage={usage} />
        </section>
      </div>
    </main>
  );
}

"use client";

import { useState } from "react";
import type { ModelConfig } from "@/lib/admin-api";

interface Props {
  models: ModelConfig[];
  onSave: (model: ModelConfig) => void;
  onDelete: (id: string) => void;
}

const EMPTY_MODEL: ModelConfig = {
  id: "",
  display_name: "",
  litellm_model: "",
  api_key: "",
  api_base: null,
  max_tokens: 4096,
  default_temperature: 0.7,
  cost_per_1k_input: 0,
  cost_per_1k_output: 0,
  is_active: true,
};

export default function ModelConfigPanel({ models, onSave, onDelete }: Props) {
  const [editing, setEditing] = useState<ModelConfig | null>(null);
  const [showForm, setShowForm] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editing && editing.id && editing.litellm_model) {
      onSave(editing);
      setEditing(null);
      setShowForm(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">模型配置</h3>
        <button
          onClick={() => { setEditing({ ...EMPTY_MODEL }); setShowForm(true); }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
        >
          + 添加模型
        </button>
      </div>

      {showForm && editing && (
        <form onSubmit={handleSubmit} className="mb-6 p-4 border rounded-lg bg-gray-50 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">ID（唯一标识）</label>
              <input value={editing.id} onChange={(e) => setEditing({ ...editing, id: e.target.value })}
                className="w-full p-2 border rounded text-sm" placeholder="gpt-4o" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">显示名称</label>
              <input value={editing.display_name} onChange={(e) => setEditing({ ...editing, display_name: e.target.value })}
                className="w-full p-2 border rounded text-sm" placeholder="GPT-4o" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">LiteLLM模型ID</label>
              <input value={editing.litellm_model} onChange={(e) => setEditing({ ...editing, litellm_model: e.target.value })}
                className="w-full p-2 border rounded text-sm" placeholder="gpt-4o" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">API Key</label>
              <input type="password" value={editing.api_key} onChange={(e) => setEditing({ ...editing, api_key: e.target.value })}
                className="w-full p-2 border rounded text-sm" placeholder="sk-..." />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">API Base（可选）</label>
              <input value={editing.api_base || ""} onChange={(e) => setEditing({ ...editing, api_base: e.target.value || null })}
                className="w-full p-2 border rounded text-sm" placeholder="https://api.example.com/v1" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">默认温度</label>
              <input type="number" step="0.1" min="0" max="2" value={editing.default_temperature}
                onChange={(e) => setEditing({ ...editing, default_temperature: parseFloat(e.target.value) })}
                className="w-full p-2 border rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">输入成本 ($/1K tokens)</label>
              <input type="number" step="0.001" min="0" value={editing.cost_per_1k_input}
                onChange={(e) => setEditing({ ...editing, cost_per_1k_input: parseFloat(e.target.value) })}
                className="w-full p-2 border rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">输出成本 ($/1K tokens)</label>
              <input type="number" step="0.001" min="0" value={editing.cost_per_1k_output}
                onChange={(e) => setEditing({ ...editing, cost_per_1k_output: parseFloat(e.target.value) })}
                className="w-full p-2 border rounded text-sm" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700">保存</button>
            <button type="button" onClick={() => { setShowForm(false); setEditing(null); }}
              className="px-4 py-2 bg-gray-300 rounded text-sm hover:bg-gray-400">取消</button>
          </div>
        </form>
      )}

      <div className="space-y-2">
        {models.map((m) => (
          <div key={m.id} className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <span className="font-medium">{m.display_name}</span>
              <span className="ml-2 text-sm text-gray-500">{m.litellm_model}</span>
              <span className={`ml-2 text-xs px-2 py-0.5 rounded ${m.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                {m.is_active ? "启用" : "禁用"}
              </span>
            </div>
            <div className="flex gap-2">
              <button onClick={() => { setEditing({ ...m }); setShowForm(true); }}
                className="text-sm text-blue-600 hover:underline">编辑</button>
              <button onClick={() => onDelete(m.id)}
                className="text-sm text-red-600 hover:underline">删除</button>
            </div>
          </div>
        ))}
        {models.length === 0 && (
          <p className="text-gray-400 text-center py-4">暂无模型配置，请添加</p>
        )}
      </div>
    </div>
  );
}

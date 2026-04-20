"use client";

import { useCallback, useEffect, useState, use } from "react";
import Link from "next/link";
import { getStoryBible, updateBible } from "@/lib/api";

export default function OutlineEditorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: storyId } = use(params);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [bible, setBible] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState("basic");

  useEffect(() => {
    getStoryBible(storyId).then(setBible).catch(console.error);
  }, [storyId]);

  const handleSave = async () => {
    if (!bible) return;
    setSaving(true);
    setMessage(null);
    try {
      await updateBible(storyId, bible);
      setMessage("保存成功");
      setTimeout(() => setMessage(null), 3000);
    } catch (e) {
      setMessage(`保存失败: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  const update = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (path: string, value: any) => {
      setBible((prev: any) => {
        if (!prev) return prev;
        const copy = JSON.parse(JSON.stringify(prev));
        const parts = path.split(".");
        let obj = copy;
        for (let i = 0; i < parts.length - 1; i++) {
          if (!obj[parts[i]]) obj[parts[i]] = {};
          obj = obj[parts[i]];
        }
        obj[parts[parts.length - 1]] = value;
        return copy;
      });
    },
    []
  );

  if (!bible) {
    return (
      <main className="max-w-4xl mx-auto p-8">
        <p className="text-gray-500">加载中...</p>
      </main>
    );
  }

  const sections = [
    { id: "basic", label: "基本信息" },
    { id: "world", label: "世界观" },
    { id: "characters", label: "角色" },
    { id: "volumes", label: "分卷大纲" },
  ];

  return (
    <main className="max-w-5xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href={`/stories/${storyId}`} className="text-blue-600 hover:underline text-sm">
            &larr; 返回故事
          </Link>
          <h1 className="text-xl font-bold">编辑大纲：《{bible.title}》</h1>
        </div>
        <div className="flex items-center gap-3">
          {message && (
            <span className={`text-sm ${message.includes("失败") ? "text-red-600" : "text-green-600"}`}>
              {message}
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-400 transition"
          >
            {saving ? "保存中..." : "保存"}
          </button>
        </div>
      </div>

      {/* Section tabs */}
      <div className="flex gap-1 mb-6 border-b">
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => setActiveSection(s.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
              activeSection === s.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* === Basic Info === */}
      {activeSection === "basic" && (
        <div className="space-y-4">
          <Field label="书名" value={bible.title} onChange={(v) => update("title", v)} />
          <div className="grid grid-cols-2 gap-4">
            <Field label="题材" value={bible.genre} onChange={(v) => update("genre", v)} />
            <Field label="基调" value={bible.tone} onChange={(v) => update("tone", v)} />
          </div>
          <Field label="一句话概述" value={bible.one_line_summary} onChange={(v) => update("one_line_summary", v)} />
          <FieldArea label="故事梗概" value={bible.synopsis} onChange={(v) => update("synopsis", v)} rows={4} />
          <FieldArea label="完整叙事概要" value={bible.inspiration} onChange={(v) => update("inspiration", v)} rows={8} />
          <FieldArea label="总体故事弧线" value={bible.planned_arc} onChange={(v) => update("planned_arc", v)} rows={3} />
        </div>
      )}

      {/* === World === */}
      {activeSection === "world" && (
        <div className="space-y-4">
          <FieldArea
            label="世界观背景"
            value={bible.world?.world_background}
            onChange={(v) => update("world.world_background", v)}
            rows={5}
          />
          <h3 className="font-medium text-sm text-gray-600 mt-4">金手指</h3>
          <div className="pl-4 border-l-2 border-amber-300 space-y-3">
            <Field
              label="名称"
              value={bible.world?.special_ability?.name}
              onChange={(v) => {
                const sa = { ...bible.world?.special_ability, name: v };
                update("world.special_ability", sa);
              }}
            />
            <FieldArea
              label="描述"
              value={bible.world?.special_ability?.description}
              onChange={(v) => {
                const sa = { ...bible.world?.special_ability, description: v };
                update("world.special_ability", sa);
              }}
              rows={2}
            />
            <FieldList
              label="功能列表"
              items={bible.world?.special_ability?.functions || []}
              onChange={(items) => {
                const sa = { ...bible.world?.special_ability, functions: items };
                update("world.special_ability", sa);
              }}
            />
          </div>

          <h3 className="font-medium text-sm text-gray-600 mt-4">势力</h3>
          {(bible.world?.factions || []).map((f: any, i: number) => (
            <div key={i} className="pl-4 border-l-2 border-gray-200 space-y-2">
              <div className="flex gap-3">
                <Field label="名称" value={f.name} onChange={(v) => {
                  const factions = [...(bible.world?.factions || [])];
                  factions[i] = { ...factions[i], name: v };
                  update("world.factions", factions);
                }} />
                <Field label="立场" value={f.stance} onChange={(v) => {
                  const factions = [...(bible.world?.factions || [])];
                  factions[i] = { ...factions[i], stance: v };
                  update("world.factions", factions);
                }} />
              </div>
              <FieldArea label="描述" value={f.description} onChange={(v) => {
                const factions = [...(bible.world?.factions || [])];
                factions[i] = { ...factions[i], description: v };
                update("world.factions", factions);
              }} rows={2} />
            </div>
          ))}
          <button
            onClick={() => update("world.factions", [...(bible.world?.factions || []), { name: "", description: "", stance: "neutral" }])}
            className="text-sm text-blue-600 hover:underline"
          >
            + 添加势力
          </button>
        </div>
      )}

      {/* === Characters === */}
      {activeSection === "characters" && (
        <div className="space-y-6">
          {["protagonist", "antagonist"].map((role) => {
            const char = bible[role];
            if (!char) return null;
            return (
              <CharacterEditor
                key={role}
                label={role === "protagonist" ? "主角" : "反派"}
                char={char}
                onChange={(updated) => update(role, updated)}
              />
            );
          })}
          <h3 className="font-medium text-sm text-gray-600">配角</h3>
          {(bible.supporting_characters || []).map((c: any, i: number) => (
            <CharacterEditor
              key={i}
              label={`配角 ${i + 1}`}
              char={c}
              onChange={(updated) => {
                const chars = [...(bible.supporting_characters || [])];
                chars[i] = updated;
                update("supporting_characters", chars);
              }}
            />
          ))}
          <button
            onClick={() =>
              update("supporting_characters", [
                ...(bible.supporting_characters || []),
                { character_id: `char_support_${(bible.supporting_characters?.length || 0) + 1}`, name: "", role: "supporting", personality: "", background: "", goals: [], weaknesses: [] },
              ])
            }
            className="text-sm text-blue-600 hover:underline"
          >
            + 添加配角
          </button>
        </div>
      )}

      {/* === Volumes === */}
      {activeSection === "volumes" && (
        <div className="space-y-6">
          {(bible.volumes || []).map((vol: any, i: number) => (
            <div key={i} className="border rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-3">
                <Field label="卷名" value={vol.volume_name} onChange={(v) => {
                  const vols = [...(bible.volumes || [])];
                  vols[i] = { ...vols[i], volume_name: v };
                  update("volumes", vols);
                }} />
                <Field label="起始章" value={String(vol.chapter_start || "")} onChange={(v) => {
                  const vols = [...(bible.volumes || [])];
                  vols[i] = { ...vols[i], chapter_start: parseInt(v) || 1 };
                  update("volumes", vols);
                }} />
                <Field label="结束章" value={String(vol.chapter_end || "")} onChange={(v) => {
                  const vols = [...(bible.volumes || [])];
                  vols[i] = { ...vols[i], chapter_end: parseInt(v) || 30 };
                  update("volumes", vols);
                }} />
              </div>
              <FieldArea label="主线剧情" value={vol.main_plot} onChange={(v) => {
                const vols = [...(bible.volumes || [])];
                vols[i] = { ...vols[i], main_plot: v };
                update("volumes", vols);
              }} rows={4} />
              <FieldList label="支线剧情" items={vol.subplots || []} onChange={(items) => {
                const vols = [...(bible.volumes || [])];
                vols[i] = { ...vols[i], subplots: items };
                update("volumes", vols);
              }} />
              <FieldList label="矛盾冲突" items={vol.conflicts || []} onChange={(items) => {
                const vols = [...(bible.volumes || [])];
                vols[i] = { ...vols[i], conflicts: items };
                update("volumes", vols);
              }} />
              <Field label="高潮事件" value={vol.climax_event} onChange={(v) => {
                const vols = [...(bible.volumes || [])];
                vols[i] = { ...vols[i], climax_event: v };
                update("volumes", vols);
              }} />
            </div>
          ))}
          <button
            onClick={() =>
              update("volumes", [
                ...(bible.volumes || []),
                { volume_num: (bible.volumes?.length || 0) + 1, volume_name: "", chapter_start: 1, chapter_end: 30, main_plot: "", subplots: [], conflicts: [], climax_event: "" },
              ])
            }
            className="text-sm text-blue-600 hover:underline"
          >
            + 添加卷
          </button>
        </div>
      )}
    </main>
  );
}

// === Helper components ===

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex-1">
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <input
        type="text"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2 border rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
      />
    </div>
  );
}

function FieldArea({ label, value, onChange, rows = 3 }: { label: string; value: string; onChange: (v: string) => void; rows?: number }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <textarea
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="w-full p-2 border rounded text-sm resize-vertical focus:ring-2 focus:ring-blue-500 focus:outline-none"
      />
    </div>
  );
}

function FieldList({ label, items, onChange }: { label: string; items: string[]; onChange: (items: string[]) => void }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <div className="space-y-1.5">
        {items.map((item, i) => (
          <div key={i} className="flex gap-2">
            <input
              type="text"
              value={item}
              onChange={(e) => {
                const copy = [...items];
                copy[i] = e.target.value;
                onChange(copy);
              }}
              className="flex-1 p-2 border rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <button
              onClick={() => onChange(items.filter((_, j) => j !== i))}
              className="text-red-400 hover:text-red-600 text-sm px-2"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          onClick={() => onChange([...items, ""])}
          className="text-xs text-blue-600 hover:underline"
        >
          + 添加
        </button>
      </div>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CharacterEditor({ label, char, onChange }: { label: string; char: any; onChange: (c: any) => void }) {
  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-xs px-2 py-0.5 rounded ${
          char.role === "protagonist" ? "bg-amber-100 text-amber-700"
          : char.role === "antagonist" ? "bg-red-100 text-red-700"
          : "bg-gray-100 text-gray-600"
        }`}>{label}</span>
        <span className="text-sm font-medium">{char.name || "(未命名)"}</span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Field label="姓名" value={char.name} onChange={(v) => onChange({ ...char, name: v })} />
        <Field label="性别" value={char.gender} onChange={(v) => onChange({ ...char, gender: v })} />
        <Field label="年龄" value={char.age} onChange={(v) => onChange({ ...char, age: v })} />
      </div>
      <FieldArea label="外貌" value={char.appearance} onChange={(v) => onChange({ ...char, appearance: v })} rows={2} />
      <FieldArea label="性格" value={char.personality} onChange={(v) => onChange({ ...char, personality: v })} rows={2} />
      <FieldArea label="背景" value={char.background} onChange={(v) => onChange({ ...char, background: v })} rows={3} />
      <FieldList label="目标" items={char.goals || []} onChange={(items) => onChange({ ...char, goals: items })} />
      <FieldList label="弱点" items={char.weaknesses || []} onChange={(items) => onChange({ ...char, weaknesses: items })} />
      <Field label="人物弧线" value={char.arc_plan} onChange={(v) => onChange({ ...char, arc_plan: v })} />

      <div className="pt-3 mt-3 border-t border-dashed border-gray-200">
        <div className="text-xs text-gray-500 mb-2">以下字段用于长线一致性（Writer 会严格遵守）</div>
        <FieldList
          label="示例台词（完整句子，体现语气）"
          items={char.speech_examples || []}
          onChange={(items) => onChange({ ...char, speech_examples: items })}
        />
        <FieldList
          label="说话硬规则（可验证的行为准则）"
          items={char.speech_rules || []}
          onChange={(items) => onChange({ ...char, speech_rules: items })}
        />
        <FieldList
          label="习惯动作 / 口头禅"
          items={char.mannerisms || []}
          onChange={(items) => onChange({ ...char, mannerisms: items })}
        />
        <FieldList
          label="不可违反的设定底线"
          items={char.hard_constraints || []}
          onChange={(items) => onChange({ ...char, hard_constraints: items })}
        />
      </div>
    </div>
  );
}

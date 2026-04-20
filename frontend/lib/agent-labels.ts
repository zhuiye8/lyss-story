/**
 * Agent 中文（英文）名称映射。
 * 用于日志页、用量统计、Agent 绑定面板、LLM 成本面板等处。
 */

/** 当前活跃的 agent — 可配置模型 */
export const AGENT_LABELS: Record<string, string> = {
  // Init pipeline
  concept:             "概念设计（concept）",
  world_builder:       "世界观构建（world_builder）",
  character_designer:  "角色设计（character_designer）",
  outline_planner:     "大纲规划（outline_planner）",
  outline_parser:      "大纲解析（outline_parser）",
  // Chapter pipeline
  world:               "世界推进（world）",
  planner:             "剧情规划（planner）",
  camera:              "视角决策（camera）",
  consistency:         "一致性检查（consistency）",
  titler:              "章节命名（titler）",
  character_arc:       "角色弧线（character_arc）",
  // Scene-level
  scene_splitter:      "场景拆分（scene_splitter）",
  scene_writer:        "场景写作（scene_writer）",
  scene_consistency:   "场景校验（scene_consistency）",
  // Helpers
  extractor:           "记忆提取（extractor）",
  character_reviewer:  "角色状态更新（character_reviewer）",
};

/** 已废弃的 agent — 不可配置，仅用于历史日志显示 */
export const DEPRECATED_LABELS: Record<string, string> = {
  director:            "导演-已废弃（director）",
  writer:              "写作-已废弃（writer）",
  outline_enricher:    "大纲补全-已废弃（outline_enricher）",
};

/** 合并活跃 + 废弃，用于日志/统计中查找任意 agent 名 */
const ALL_LABELS: Record<string, string> = { ...AGENT_LABELS, ...DEPRECATED_LABELS };

/**
 * 获取 agent 的显示名。未知 key 返回原始 key。
 */
export function agentLabel(key: string): string {
  return ALL_LABELS[key] || key;
}

/**
 * 活跃 agent key 列表（用于绑定配置下拉等）。
 */
export const ALL_AGENT_KEYS = Object.keys(AGENT_LABELS);

/**
 * 废弃 agent key 列表。
 */
export const DEPRECATED_AGENT_KEYS = Object.keys(DEPRECATED_LABELS);

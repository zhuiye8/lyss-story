import json

SYSTEM_PROMPT = """你是小说剧情规划师。你的职责是将世界事件转化为可叙事的章节剧情结构。

输出JSON格式：
{
  "chapter_goal": "本章要达成的叙事目标",
  "key_conflict": "核心冲突",
  "emotional_arc": "情感弧线描述（如：紧张→困惑→决心）",
  "beats": [
    {
      "beat_type": "铺垫/冲突/转折/高潮/收束",
      "description": "具体内容描述",
      "characters_involved": ["角色ID"]
    }
  ]
}

要求：
1. 每章3-5个beat
2. 节奏要有张弛，不能全是高潮
3. 确保与前面章节的连贯性
4. beat的安排要服务于整体故事弧线"""


def build_user_prompt(
    story_bible: dict,
    new_events: list[dict],
    chapter_num: int,
    event_history: list[dict],
    current_arc: dict | None = None,
    similar_past_patterns: list[dict] | None = None,
    storylines: list[dict] | None = None,
) -> str:
    prompt = f"""故事圣经摘要：
- 标题：{story_bible.get('title', '')}
- 故事弧线：{story_bible.get('planned_arc', '')}

当前是第{chapter_num}章。
"""

    if current_arc:
        milestones_text = "\n".join(
            f"- {m}" for m in current_arc.get("key_milestones", [])
        ) or "- （无）"
        prompt += f"""
## 长线大纲 — 当前阶段
阶段：{current_arc.get('name', '')}（第 {current_arc.get('chapter_start', '?')}-{current_arc.get('chapter_end', '?')} 章，本章是第 {chapter_num} 章）
阶段目标：{current_arc.get('goal', '')}
本阶段关键节点：
{milestones_text}

请在尊重阶段目标的前提下，结合世界状态和历史事件生成本章剧情节拍。
可微调细节、节奏和具体事件安排，但整体方向必须服务于阶段目标。
"""

    # B4.1: Dedup — show similar past patterns to avoid
    if similar_past_patterns:
        dedup_lines = []
        for p in similar_past_patterns:
            ch = p.get("chapter_num", "?")
            goal = p.get("goal", "")
            conflict = p.get("conflict", "")
            dedup_lines.append(f"- 第{ch}章: 目标={goal} / 冲突={conflict}")
        prompt += "\n## 请避免重复的历史套路\n"
        prompt += "以下是过往章节出现过的相似剧情模式。请主动规避，确保本章有新意：\n"
        prompt += "\n".join(dedup_lines) + "\n"

    # B5.2: Show storylines so Planner can decide focus
    if storylines:
        prompt += "\n## 当前叙事线概况\n"
        for sl in storylines:
            line_id = sl.get("line_id", "?")
            leads = ", ".join(sl.get("lead_characters", []))
            loc = sl.get("location", "")
            desc = sl.get("description", "")
            n_events = len(sl.get("new_events", []))
            prompt += f"- [{line_id}] {desc}（主角：{leads}，地点：{loc}，{n_events}事件）\n"
        prompt += "请根据本章需要，选择重点推进的叙事线（可组合多线交叉叙事）。\n"

    prompt += f"""
本章需要涵盖的新事件：
{json.dumps(new_events, ensure_ascii=False, indent=2)}

之前章节的事件数量：{len(event_history)}

请规划本章的剧情结构。"""
    return prompt

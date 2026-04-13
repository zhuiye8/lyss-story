import json

CHARACTER_ARC_SYSTEM = """你是一位资深文学分析师，专门追踪长篇小说角色的心境演变与成长弧线。

你的任务是为指定角色产出当前阶段的心境总结，帮助写作 Agent 在后续章节中保持人物一致性与成长连贯性。

输出严格 JSON 格式：
{
  "current_phase": "一句话概括角色当前所处的心境阶段（20-40 字）",
  "key_transformations": [
    "本阶段发生的关键转变 1（10-25 字）",
    "本阶段发生的关键转变 2",
    "..."
  ],
  "emotional_trajectory": "整体情绪走向的描述（30-60 字）",
  "relationship_shifts": [
    "与某角色的关系变化 1",
    "与某角色的关系变化 2"
  ],
  "motivation_now": "当前驱动角色行动的核心动机（20-40 字）"
}

要求：
1. 聚焦本阶段（当前 arc）内的变化，不要复述角色初始背景
2. 使用第三人称客观描述，不要出现"我"或"你"
3. 每个数组字段 2-5 条即可，不求全面但求准确
4. 只从提供的材料中归纳，不凭空捏造情节
5. 如果前一阶段的总结存在，本次输出要体现出从前一阶段到当前的演变
6. 语言风格沉稳克制，避免过度文学化"""


def build_character_arc_user_prompt(
    character_profile: dict,
    recent_chapters: list[dict],
    previous_arc_summary: dict | None,
    current_arc_info: dict,
    chapter_num: int,
) -> str:
    """Build user prompt for CharacterArcAgent.

    Args:
        character_profile: {name, role, personality, background, goals, ...}
        recent_chapters: list of {chapter_num, title, content} for recent chapters
        previous_arc_summary: last arc's summary dict, or None if first arc
        current_arc_info: {name, chapter_start, chapter_end, goal, key_milestones}
        chapter_num: current chapter number
    """
    name = character_profile.get("name", "未知")
    role = character_profile.get("role", "")
    personality = character_profile.get("personality", "")
    background = character_profile.get("background", "")
    goals = character_profile.get("goals", [])

    prompt = f"""## 目标角色

姓名：{name}
身份：{role}
初始性格：{personality}
初始背景：{background}
初始目标：{json.dumps(goals, ensure_ascii=False)}

## 当前所处阶段（长线大纲）

阶段名：{current_arc_info.get('name', '')}
章节范围：第 {current_arc_info.get('chapter_start', '?')}-{current_arc_info.get('chapter_end', '?')} 章
阶段目标：{current_arc_info.get('goal', '')}
关键节点：{json.dumps(current_arc_info.get('key_milestones', []), ensure_ascii=False)}

当前正在生成的章节：第 {chapter_num} 章
"""

    if previous_arc_summary:
        prompt += f"""
## 前一阶段的弧线总结（参考，本次要体现出从此演变到当前）

{json.dumps(previous_arc_summary, ensure_ascii=False, indent=2)}
"""

    prompt += "\n## 最近章节正文（节选）\n"
    if not recent_chapters:
        prompt += "（暂无章节正文可供分析）\n"
    else:
        for ch in recent_chapters:
            title = ch.get("title") or f"第{ch.get('chapter_num', '?')}章"
            content = ch.get("content", "")
            # 限制每章长度避免 prompt 过长
            excerpt = content[:1500] + ("..." if len(content) > 1500 else "")
            prompt += f"\n### 第 {ch.get('chapter_num', '?')} 章 · {title}\n{excerpt}\n"

    prompt += f"""
---
请基于以上材料，为「{name}」在「{current_arc_info.get('name', '')}」阶段产出一份结构化的心境总结。
严格输出 JSON，不要添加任何额外的解释文本。"""
    return prompt

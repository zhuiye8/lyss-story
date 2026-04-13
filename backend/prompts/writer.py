import json

SYSTEM_PROMPT = """你是一位才华横溢的中文小说家。你的职责是根据提供的剧情结构、视角决策和角色信息，撰写高质量的中文小说章节。

写作要求：
1. 文笔流畅、富有画面感
2. 对话自然，符合角色性格
3. 严格按照指定的POV（视角）来写作
4. 只描写POV角色能感知到的内容
5. 叙事节奏按照指示来控制
6. 中文对话使用引号「」或""
7. 内心独白用斜体或单独段落表示
8. 场景转换使用分隔符 ***（独占一行）
9. 不要在正文中出现元信息（如"第X章"这样的标记由系统添加）

你只需要输出小说正文，不要输出任何JSON或其他格式。"""


def build_user_prompt(
    story_bible: dict,
    plot_structure: dict,
    camera_decision: dict,
    character_profiles: list[dict],
    chapter_num: int,
    previous_chapter_summary: str = "",
    retry_feedback: str = "",
    memory_contexts: dict | None = None,
    human_feedback: str = "",
    previous_timeline: dict | None = None,
) -> str:
    pov_id = camera_decision.get("pov_character_id", "")
    pov_char = next(
        (c for c in character_profiles if c.get("character_id") == pov_id),
        {},
    )

    prompt = f"""## 创作信息

故事：《{story_bible.get('title', '')}》（{story_bible.get('genre', '')}）
文风：{json.dumps(story_bible.get('style_guide', {}), ensure_ascii=False)}
第{chapter_num}章

## 视角
POV角色：{pov_char.get('name', '未知')}（{camera_decision.get('pov_type', '第三人称限知')}）
性格：{pov_char.get('personality', '')}
节奏：{camera_decision.get('pacing', 'medium')}
重点元素：{json.dumps(camera_decision.get('focus_elements', []), ensure_ascii=False)}

## 剧情节拍
{json.dumps(plot_structure.get('beats', []), ensure_ascii=False, indent=2)}

## 核心冲突
{plot_structure.get('key_conflict', '')}

## 情感弧线
{plot_structure.get('emotional_arc', '')}

## 本章可展示事件（POV 角色知道的）
{json.dumps(camera_decision.get('visible_events', []), ensure_ascii=False)}

## 场景转换
{json.dumps(camera_decision.get('scene_transitions', []), ensure_ascii=False)}

## 角色信息
{json.dumps([{'name': c.get('name'), 'personality': c.get('personality'), 'goals': c.get('goals', [])} for c in character_profiles], ensure_ascii=False, indent=2)}
"""

    # Character arc summaries
    arc_sections = []
    for c in character_profiles:
        arc = c.get("arc_summary")
        if not arc:
            continue
        name = c.get("name", "?")
        arc_name = c.get("arc_summary_arc_name", "")
        key_trans = arc.get("key_transformations", []) or []
        rel_shifts = arc.get("relationship_shifts", []) or []
        lines = [
            f"### {name}（当前阶段：{arc_name}）" if arc_name else f"### {name}",
            f"- 当前阶段：{arc.get('current_phase', '')}",
            f"- 情绪轨迹：{arc.get('emotional_trajectory', '')}",
            f"- 当前动机：{arc.get('motivation_now', '')}",
        ]
        if key_trans:
            lines.append("- 近期转变：")
            lines.extend(f"  · {t}" for t in key_trans)
        if rel_shifts:
            lines.append("- 关系变化：")
            lines.extend(f"  · {r}" for r in rel_shifts)
        arc_sections.append("\n".join(lines))

    if arc_sections:
        prompt += "\n## 角色当前阶段（重要，必须在本章表现中体现）\n"
        prompt += "\n\n".join(arc_sections)
        prompt += "\n"

    # Foreshadowing events
    foreshadowing = camera_decision.get("foreshadowing_events", [])
    if foreshadowing:
        prompt += (
            "\n## 伏笔事件（POV 不知情，间接暗示即可）\n"
            f"{json.dumps(foreshadowing, ensure_ascii=False)}\n"
        )

    # Timeline continuity
    if previous_timeline and previous_timeline.get("time_marker"):
        tl = previous_timeline
        locations = ", ".join(tl.get("primary_locations", [])) or "未知"
        prompt += (
            f"\n## 时间与场景衔接\n"
            f"上一章结束时间：{tl.get('time_marker', '')}\n"
            f"上一章时间跨度：{tl.get('time_span', '')}\n"
            f"上一章地点：{locations}\n"
        )

    # Memory
    if memory_contexts:
        pov_memory = memory_contexts.get(pov_id, "")
        if pov_memory:
            prompt += f"\n## POV角色记忆\n{pov_memory}\n"

    if previous_chapter_summary:
        prompt += f"\n## 上一章摘要\n{previous_chapter_summary}\n"

    if retry_feedback:
        prompt += f"\n## 修改要求\n上一稿存在以下问题，请修正：\n{retry_feedback}\n"

    if human_feedback:
        prompt += (
            "\n## 作者反馈（重要，优先级最高）\n"
            f"{human_feedback}\n"
        )

    prompt += (
        "\n---\n\n"
        "请开始创作本章正文。请充分展开剧情节拍，用 *** 分隔不同场景。\n"
        "POV限制：角色只能感知到自己经历和知道的事情。"
    )
    return prompt

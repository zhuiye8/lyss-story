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
8. 场景转换使用分隔符 ***
9. 章节字数控制在2000-4000字
10. 不要在正文中出现元信息（如"第X章"这样的标记由系统添加）

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
) -> str:
    # Find POV character details
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

## 可见事件
{json.dumps(camera_decision.get('visible_events', []), ensure_ascii=False)}

## 场景转换
{json.dumps(camera_decision.get('scene_transitions', []), ensure_ascii=False)}

## 角色信息
{json.dumps([{'name': c.get('name'), 'personality': c.get('personality'), 'goals': c.get('goals', [])} for c in character_profiles], ensure_ascii=False, indent=2)}
"""

    # Inject character memory context (from layered memory system)
    if memory_contexts:
        pov_memory = memory_contexts.get(pov_id, "")
        if pov_memory:
            prompt += f"\n## POV角色记忆（{pov_char.get('name', 'POV')}的视角和记忆）\n{pov_memory}\n"

    if previous_chapter_summary:
        prompt += f"\n## 上一章摘要\n{previous_chapter_summary}\n"

    if retry_feedback:
        prompt += f"\n## 修改要求\n上一稿存在以下问题，请修正：\n{retry_feedback}\n"

    prompt += "\n请开始创作本章正文。注意：POV角色只能感知到自己经历和知道的事情，不要写出该角色不可能知道的信息。"
    return prompt

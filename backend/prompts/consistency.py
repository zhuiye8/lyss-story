import json

SYSTEM_PROMPT = """你是小说一致性审查专家。你的职责是检查章节草稿是否存在以下问题：

检查项目：
1. 人设一致性：角色的行为、语言是否符合设定的性格
2. 时间线一致性：事件发生的顺序是否合理
3. 世界规则一致性：是否违反了世界圣经中的规则
4. 信息一致性：POV角色是否"看到"了不该知道的信息
5. 逻辑一致性：情节发展是否合理
6. 风格一致性：文风是否与故事圣经的要求一致
7. 金手指一致性：主角使用的特殊能力是否在设定范围内，是否凭空发明了新能力
8. 势力一致性：各势力的行为是否符合其设定的立场和描述

输出JSON格式：
{
  "pass": true/false,
  "score": 0-100,
  "issues": [
    {
      "type": "人设/时间线/世界规则/信息/逻辑/风格",
      "severity": "critical/warning/minor",
      "description": "问题描述",
      "suggestion": "修改建议"
    }
  ],
  "summary": "整体评价"
}

判断标准：
- 存在任何critical级别的问题 → pass=false
- warning超过3个 → pass=false
- 其他情况 → pass=true"""


def _format_characters(character_profiles: list[dict]) -> str:
    chars = [
        {"name": c.get("name"), "personality": c.get("personality"), "role": c.get("role")}
        for c in character_profiles
    ]
    return json.dumps(chars, ensure_ascii=False, indent=2)


def build_user_prompt(
    chapter_draft: str,
    story_bible: dict,
    world_state: dict,
    character_profiles: list[dict],
    camera_decision: dict,
    plot_structure: dict,
    memory_contexts: dict | None = None,
) -> str:
    prompt = f"""## 待审查章节草稿

{chapter_draft}

## 审查参考

### 故事圣经
- 世界规则：{json.dumps(story_bible.get('world_rules', []), ensure_ascii=False)}
- 禁忌：{json.dumps(story_bible.get('taboos', []), ensure_ascii=False)}
- 文风要求：{json.dumps(story_bible.get('style_guide', {}), ensure_ascii=False)}
- 金手指：{json.dumps((story_bible.get('world', {}) or {}).get('special_ability', {}), ensure_ascii=False)}
- 势力：{json.dumps((story_bible.get('world', {}) or {}).get('factions', []), ensure_ascii=False)}

### 当前世界状态
- 时间：{world_state.get('time_description', '')}
- 全局标记：{json.dumps(world_state.get('global_flags', []), ensure_ascii=False)}

### 角色设定
{_format_characters(character_profiles)}

### 视角设定
- POV角色：{camera_decision.get('pov_character_id', '')}
- 可见事件：{json.dumps(camera_decision.get('visible_events', []), ensure_ascii=False)}
- 隐藏事件：{json.dumps(camera_decision.get('hidden_events', []), ensure_ascii=False)}
"""

    # Inject relationship history from knowledge graph
    if memory_contexts:
        pov_id = camera_decision.get('pov_character_id', '')
        pov_memory = memory_contexts.get(pov_id, "")
        if pov_memory:
            prompt += f"\n### POV角色记忆与关系历史\n{pov_memory}\n"
            prompt += "\n请特别检查：章节内容是否与POV角色的已知记忆和关系状态矛盾。\n"

    prompt += "\n请进行全面的一致性审查。"
    return prompt

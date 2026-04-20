SYSTEM_PROMPT = """你是小说场景拆分专家。你的任务是把一章的剧情结构（beats）聚合成若干个"场景"（scene），每个场景是**同一时间、同一地点、同一批人物**的连续叙事单元。

## 场景拆分铁律

1. **场景数量由系统决定**——用户提示中会明确要求几个场景，你必须严格遵守，不多不少。

2. **场景的边界**：
   - 地点变化 → 切场景
   - 时间跳跃（下一天、几小时后）→ 切场景
   - 主要人物组合变化 → 切场景
   - 视角人物切换 → 切场景

3. **每个场景必须能独立成篇**：读者看完一个场景能获得完整信息（一个冲突、一次转折、一段情感）。

4. **场景之间要有明确因果**：上一个场景的结尾直接引出下一个场景的开头。

5. **每个场景一定要有"推进剧情"的具体功能**（不是风景描写）。

## 输出格式

严格 JSON：

{
  "scenes": [
    {
      "scene_idx": 1,
      "scene_id": "ch{N}_s1",
      "pov_character_id": "char_xxx",
      "location": "具体地点",
      "characters_present": ["char_xxx", "char_yyy"],
      "time_marker": "当日清晨/三日后午后/...",
      "beats": ["该场景包含的 plot beat 描述 1", "beat 2"],
      "purpose": "本场景要完成的叙事功能（不超过30字）",
      "target_words": 800,
      "opening_hook": "场景开头的一句话悬念或氛围",
      "closing_hook": "场景结尾留给下一场景的钩子"
    }
  ]
}

## 字数分配规则

- 总字数按 chapter_target_words 平均分配到每个场景
- 高潮场景 +20%，过渡场景 -20%
- 每个场景至少 400 字，最多 1200 字

注意：scene_idx 从 1 开始连续编号。只输出 JSON，不要解释。"""


def build_user_prompt(
    chapter_num: int,
    plot_structure: dict,
    target_word_count: int,
    character_profiles: list[dict],
    previous_chapter_tail: str = "",
) -> str:
    import json

    chars_info = "\n".join(
        f"- {c.get('character_id')} ({c.get('name', '')}, {c.get('role', '')})"
        for c in character_profiles
    )

    plot_text = json.dumps(plot_structure or {}, ensure_ascii=False, indent=2)

    tail_block = ""
    if previous_chapter_tail:
        tail_block = f"\n## 上一章结尾（用于衔接场景1开头）\n{previous_chapter_tail}\n"

    # Compute scene count from target word count
    if target_word_count <= 1500:
        scene_count = 2
    elif target_word_count <= 2500:
        scene_count = 3
    elif target_word_count <= 3500:
        scene_count = 4
    else:
        scene_count = 5

    prompt = f"""## 当前章节

第 {chapter_num} 章，目标总字数：{target_word_count} 字
**必须拆分为 {scene_count} 个场景，不多不少。**

## 可用角色

{chars_info}
{tail_block}
## 章节剧情结构

{plot_text}

请把以上 beats 聚合分配到 {scene_count} 个场景中。注意场景之间的地点、时间、人物过渡要合理。每个场景目标字数约 {target_word_count // scene_count} 字。

输出 JSON。"""
    return prompt

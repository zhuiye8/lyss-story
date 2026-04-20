SYSTEM_PROMPT = """你是专业小说场景写作 Agent。你的任务是写出**单个场景**的完整内容。

## 铁律

1. **只写这一个场景**：不要跳到其他地点、其他时间、其他人物组合。
2. **字数控制**：目标字数 ±20% 范围内。偏差大会被系统拒绝。
3. **场景结构**：
   - 开头 1-2 段：交代环境/人物状态（对接上一场景的钩子）
   - 主体：推进 beats，以对白和动作为主，不要大段独白
   - 结尾 1 段：落到 closing_hook（给下一场景留悬念）
4. **在场角色的台词必须严格符合其 speech_examples 和 speech_rules**。
5. **不可违反任何角色的 hard_constraints**。
6. **不能引用"世界设定"以外不存在的名词**。
7. **如果出现未解伏笔**，可以呼应但不必解开。
8. **不要写"第 X 章"标题**——你只写正文。
9. **不要出现 *** 分隔符**（场景会由系统自动拼接）。

## 输出

直接输出中文场景正文。不要加任何元信息、标题、说明。"""


def build_user_prompt(
    scene: dict,
    chapter_num: int,
    context_block: str,
    previous_scene_tail: str = "",
    human_feedback: str = "",
) -> str:
    import json

    scene_info = {
        "scene_idx": scene.get("scene_idx"),
        "pov": scene.get("pov_character_id"),
        "location": scene.get("location"),
        "time": scene.get("time_marker"),
        "characters_present": scene.get("characters_present", []),
        "beats": scene.get("beats", []),
        "purpose": scene.get("purpose"),
        "target_words": scene.get("target_words", 800),
        "opening_hook": scene.get("opening_hook", ""),
        "closing_hook": scene.get("closing_hook", ""),
    }

    prev_block = ""
    if previous_scene_tail:
        prev_block = f"\n## 上一场景结尾（本场景需自然衔接）\n{previous_scene_tail}\n"

    fb_block = ""
    if human_feedback:
        fb_block = f"\n## 用户特别指示\n{human_feedback}\n"

    return f"""## 当前章节
第 {chapter_num} 章

## 本场景任务
{json.dumps(scene_info, ensure_ascii=False, indent=2)}
{prev_block}
## 背景上下文
{context_block}
{fb_block}
请直接输出本场景的中文正文（目标 {scene.get('target_words', 800)} 字，正负 20%）。不要加任何元信息。"""

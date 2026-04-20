SYSTEM_PROMPT = """你是小说角色状态审阅 Agent。你的任务是阅读一章正文，更新一个角色的**当前动态状态**，给下一章 Writer 使用。

## 输入

- 角色卡（含 speech_examples / speech_rules / hard_constraints）
- 当前章内容
- 上一版状态（如有）

## 输出

严格 JSON：

{
  "location": "当前所在地点（章末）",
  "emotional_state": "当前主要情绪（一句话，如：因误会而愤怒/因挫败而麻木）",
  "status": "active/injured/captured/missing/dead",
  "knowledge_summary": "本章后该角色知晓的关键信息总结（1-2句话）",
  "goals_update": "目标是否变化（无变化则填：维持）",
  "current_intent": "章末时角色的即时意图（1句话，如：返回宗门复仇/寻找父亲遗物）",
  "relationship_updates": [
    {"target_id": "对方角色id", "change": "从xx变为yy", "detail": "具体原因"}
  ],
  "voice_drift_warning": "若本章中该角色台词偏离 speech_examples/rules 请在此记录（否则空字符串）"
}

原则：
1. location / current_intent 必须反映**章末**的状态，不是章中或章初
2. knowledge_summary 累积前一版本 + 本章新增
3. 不要写本章之前的信息（除非是为了说明变化）
4. voice_drift_warning 如果发现违规，明确指出哪句台词违反了哪条规则
5. 只输出 JSON"""


def build_user_prompt(
    character_profile: dict,
    chapter_content: str,
    previous_state: dict | None,
    chapter_num: int,
) -> str:
    import json

    card_info = {
        "name": character_profile.get("name"),
        "role": character_profile.get("role"),
        "speech_examples": character_profile.get("speech_examples") or [],
        "speech_rules": character_profile.get("speech_rules") or [],
        "hard_constraints": character_profile.get("hard_constraints") or [],
    }

    prev_block = "（无前置状态记录）"
    if previous_state:
        prev_block = json.dumps(
            {
                "location": previous_state.get("location"),
                "emotional_state": previous_state.get("emotional_state"),
                "status": previous_state.get("status"),
                "knowledge_summary": previous_state.get("knowledge_summary"),
                "goals_update": previous_state.get("goals_update"),
            },
            ensure_ascii=False, indent=2,
        )

    return f"""## 角色卡
{json.dumps(card_info, ensure_ascii=False, indent=2)}

## 上一版状态
{prev_block}

## 当前章（第 {chapter_num} 章）正文

{chapter_content}

请更新该角色的当前动态状态。"""

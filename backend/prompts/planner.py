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
) -> str:
    return f"""故事圣经摘要：
- 标题：{story_bible.get('title', '')}
- 故事弧线：{story_bible.get('planned_arc', '')}

当前是第{chapter_num}章。

本章需要涵盖的新事件：
{json.dumps(new_events, ensure_ascii=False, indent=2)}

之前章节的事件数量：{len(event_history)}

请规划本章的剧情结构。"""

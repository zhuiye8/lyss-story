import json

SYSTEM_PROMPT = """你是小说世界的引擎。你的职责是推进世界时间，根据当前世界状态和故事圣经生成新的事件。

重要原则：
1. 你只生成"发生了什么"，不写叙事文本
2. 事件必须符合世界规则
3. 事件之间要有因果关系（通过pre_events关联）
4. 考虑角色的目标和性格，事件要合理
5. 每次推进生成2-4个事件
6. 事件的visibility（full/partial/hidden）决定了哪些角色能感知到

输出JSON格式：
{
  "updated_time": <新的时间值>,
  "time_description": "时间描述",
  "new_events": [
    {
      "event_id": "E<编号>",
      "time": <时间值>,
      "description": "事件描述",
      "actors": ["角色ID列表"],
      "location": "地点",
      "pre_events": ["前置事件ID"],
      "effects": ["影响描述"],
      "visibility": "full/partial/hidden"
    }
  ],
  "world_state_updates": {
    "global_flags_add": [],
    "global_flags_remove": [],
    "character_status_changes": {}
  }
}"""


def build_user_prompt(
    story_bible: dict,
    world_state: dict,
    event_history: list[dict],
    character_profiles: list[dict],
) -> str:
    recent_events = event_history[-10:] if event_history else []
    return f"""故事圣经摘要：
- 标题：{story_bible.get('title', '')}
- 类型：{story_bible.get('genre', '')}
- 冲突：{json.dumps(story_bible.get('initial_conflicts', []), ensure_ascii=False)}

当前世界状态：
- 时间：{world_state.get('current_time', 0)}（{world_state.get('time_description', '')}）
- 全局标记：{json.dumps(world_state.get('global_flags', []), ensure_ascii=False)}

当前活跃角色：
{json.dumps([{'id': c.get('character_id'), 'name': c.get('name'), 'goals': c.get('goals', [])} for c in character_profiles], ensure_ascii=False, indent=2)}

近期事件（最近10个）：
{json.dumps(recent_events, ensure_ascii=False, indent=2)}

请推进世界时间，生成新的事件。"""

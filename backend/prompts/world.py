import json

SYSTEM_PROMPT = """你是小说世界的引擎。你的职责是推进世界时间，根据当前世界状态和故事圣经生成新的事件。

重要原则：
1. 你只生成"发生了什么"，不写叙事文本
2. 事件必须符合世界规则
3. 事件之间要有因果关系（通过pre_events关联）
4. 考虑角色的目标和性格，事件要合理
5. 每个事件的 visibility 决定了哪些角色能感知到这个事件

## 多叙事线（重要）
你需要按"叙事线"分组输出事件。每条叙事线有自己的主推角色和地点：
- "main" 主线：围绕主角的核心叙事
- "sub1"、"sub2"等支线：围绕其他角色或远方事件的平行叙事
- 每次至少输出主线，支线 0-2 条（视情节需要）
- 不同叙事线的事件可以发生在不同地点、不同时间
- 支线事件可以为主线埋伏笔，或在后续章节与主线交汇

## visibility 规则
每个事件必须包含结构化的 visibility 对象：
- public: true 表示"全世界都知道"（如战争爆发、公开宣告）
- public: false 时必须指定 known_to 列表，填入知情角色的 character_id

输出JSON格式：
{
  "updated_time": <新的时间值>,
  "time_description": "时间描述",
  "storylines": [
    {
      "line_id": "main",
      "lead_characters": ["主推角色ID"],
      "location": "主要地点",
      "description": "本线概述（一句话）",
      "new_events": [
        {
          "event_id": "E<编号>",
          "time": <时间值>,
          "description": "事件描述",
          "actors": ["角色ID"],
          "location": "地点",
          "pre_events": ["前置事件ID"],
          "effects": ["影响描述"],
          "visibility": { "public": false, "known_to": ["知情角色ID"] }
        }
      ]
    }
  ],
  "world_state_updates": {
    "global_flags_add": [],
    "global_flags_remove": [],
    "character_status_changes": {}
  }
}

注意：
- 主线至少2个事件，每条支线1-2个事件
- 所有叙事线的事件共享同一个 event_id 命名空间（不要重复）
- 如果故事当前阶段不需要支线，可以只输出主线"""


def build_user_prompt(
    story_bible: dict,
    world_state: dict,
    event_history: list[dict],
    character_profiles: list[dict],
) -> str:
    recent_events = event_history[-10:] if event_history else []
    world = story_bible.get("world", {})
    factions = world.get("factions", [])
    factions_text = ""
    if factions:
        factions_text = "\n势力：\n" + "\n".join(
            f"- {f.get('name', '')}（{f.get('stance', '')}）：{f.get('description', '')[:60]}"
            for f in factions
        )

    return f"""故事圣经摘要：
- 标题：{story_bible.get('title', '')}
- 类型：{story_bible.get('genre', '')}
- 冲突：{json.dumps(story_bible.get('initial_conflicts', []), ensure_ascii=False)}
{factions_text}

当前世界状态：
- 时间：{world_state.get('current_time', 0)}（{world_state.get('time_description', '')}）
- 全局标记：{json.dumps(world_state.get('global_flags', []), ensure_ascii=False)}

当前活跃角色：
{json.dumps([{'id': c.get('character_id'), 'name': c.get('name'), 'role': c.get('role', ''), 'goals': c.get('goals', []), 'location': c.get('location', '')} for c in character_profiles], ensure_ascii=False, indent=2)}

近期事件（最近10个）：
{json.dumps(recent_events, ensure_ascii=False, indent=2)}

请推进世界时间，按叙事线分组生成新的事件。事件应涉及上述势力的动态。"""

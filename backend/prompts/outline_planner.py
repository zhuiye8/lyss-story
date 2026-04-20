import json

SYSTEM_PROMPT = """你是一位小说大纲规划师。你的职责是根据已确定的核心概念、世界观和角色，规划详细的分卷大纲。

你会收到完整的故事设定（概念+世界+角色），请基于此规划分卷大纲。

输出严格 JSON：
{
  "initial_conflicts": ["核心冲突1", "核心冲突2", "冲突3"],
  "planned_arc": "总体故事弧线概述（100-200字）",
  "volumes": [
    {
      "volume_num": 1,
      "volume_name": "第一卷卷名",
      "chapter_start": 1,
      "chapter_end": 30,
      "estimated_words": 60000,
      "main_plot": "本卷主线剧情（200-500字，要具体到发生了什么事）",
      "subplots": [
        "支线1：具体到谁在哪里做了什么",
        "支线2：...",
        "支线3：...",
        "支线4：...",
        "支线5：..."
      ],
      "conflicts": [
        "矛盾冲突1：具体描述",
        "矛盾冲突2：...",
        "矛盾冲突3：..."
      ],
      "new_characters": ["本卷新登场角色名"],
      "key_locations": ["关键地点1", "地点2"],
      "climax_event": "本卷高潮事件详细描述"
    }
  ]
}

要求：
1. 至少 2 卷，每卷预计 5-10 万字
2. 每卷至少 5 条支线（subplots），要具体到"谁在哪里做了什么"
3. 每卷至少 3 条矛盾冲突（conflicts）
4. 各卷之间要有节奏起伏（如第一卷铺垫、第二卷冲突升级）
5. 每卷的 climax_event 要是关键转折点
6. 所有内容必须是中文"""


def build_user_prompt(
    concept: dict,
    world_setting: dict,
    characters_design: dict,
) -> str:
    protagonist = characters_design.get("protagonist", {})
    antagonist = characters_design.get("antagonist", {})
    supporting = characters_design.get("supporting_characters", [])
    char_summary = []
    for c in [protagonist, antagonist] + supporting:
        if c:
            char_summary.append(f"- {c.get('name', '?')}（{c.get('role', '?')}）：{c.get('personality', '')[:50]}")

    return f"""## 核心概念

书名：《{concept.get('title', '')}》
题材：{concept.get('genre', '')}
基调：{concept.get('tone', '')}
梗概：{concept.get('synopsis', '')}
金手指：{concept.get('special_ability', {}).get('name', '')}
完整故事线：{concept.get('inspiration', '')}

## 世界观

{world_setting.get('world_background', '')}
势力：{json.dumps([f.get('name', '') + '(' + f.get('stance', '') + ')' for f in world_setting.get('factions', [])], ensure_ascii=False)}

## 角色

{chr(10).join(char_summary)}

请基于以上完整设定，规划分卷大纲。"""

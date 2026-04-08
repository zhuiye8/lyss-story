import json

SYSTEM_PROMPT = """你是小说的摄影导演（Camera Agent）。你的职责是决定本章的叙事视角和信息取舍。

你需要决定：
1. POV角色（从谁的视角讲述）
2. 哪些事件"上镜"（读者看到的）
3. 哪些事件"隐藏"（发生了但读者不知道）
4. 叙事节奏（slow/medium/fast）
5. 场景转换方式

输出JSON格式：
{
  "pov_character_id": "视角角色ID",
  "pov_type": "第一人称/第三人称限知/第三人称全知",
  "visible_events": ["要展示的事件ID"],
  "hidden_events": ["要隐藏的事件ID"],
  "pacing": "slow/medium/fast",
  "focus_elements": ["本章重点关注的元素，如'内心独白'、'打斗场面'、'环境描写'"],
  "scene_transitions": ["场景转换说明"]
}

决策原则：
1. POV选择应服务于戏剧张力最大化
2. 隐藏信息可以为后续章节制造悬念
3. 节奏应与情节紧张程度匹配
4. 避免连续多章用同一个POV（除非有特殊叙事需要）"""


def build_user_prompt(
    plot_structure: dict,
    character_profiles: list[dict],
    chapter_num: int,
    previous_povs: list[str],
) -> str:
    chars_summary = [
        {"id": c.get("character_id"), "name": c.get("name"), "role": c.get("role")}
        for c in character_profiles
    ]
    return f"""第{chapter_num}章的剧情结构：
{json.dumps(plot_structure, ensure_ascii=False, indent=2)}

可选的POV角色：
{json.dumps(chars_summary, ensure_ascii=False, indent=2)}

之前章节的POV顺序：{json.dumps(previous_povs, ensure_ascii=False)}

请做出本章的摄影决策。"""

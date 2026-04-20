import json

SYSTEM_PROMPT = """你是小说的摄影导演（Camera Agent）。你的职责是决定本章的叙事视角和信息取舍。

你需要决定：
1. POV角色（从谁的视角讲述）
2. 哪些事件"上镜"（读者看到的）— 必须从提供的事件列表里选
3. 哪些事件"隐藏"（发生了但读者不知道）— 可以为后续章节制造悬念
4. 哪些事件作为"伏笔"（读者能隐约感知但 POV 角色不知情）
5. 叙事节奏（slow/medium/fast）
6. 场景转换方式

## 可见性过滤规则（重要，必须遵守）
你的分类必须只包含下方「本章新事件」列表中存在的 event_id。
选定 POV 角色后，按以下规则判断每个事件的分类：

**visible_events（POV 可见，读者可见）**：
- 事件的 visibility.public == true（公开事件，所有人都知道）
- POV 角色在事件的 actors 列表中（亲身参与/在场目击）
- POV 角色在事件的 visibility.known_to 列表中（通过消息/传闻得知）

**foreshadowing_events（POV 不可见，但读者可感知）**：
- 不满足上述可见条件，但对剧情发展至关重要
- Writer 会通过其他角色的只言片语、环境暗示、气氛描写来让读者隐约察觉
- 每章最多 1-2 个伏笔事件，不要滥用

**hidden_events（完全隐藏，本章不提及）**：
- 不满足可见条件，也不适合作为伏笔
- 留给后续章节揭露

输出JSON格式：
{
  "pov_character_id": "视角角色ID",
  "pov_type": "第一人称/第三人称限知/第三人称全知",
  "visible_events": ["POV 可见的事件ID"],
  "foreshadowing_events": ["伏笔事件ID（读者隐约感知但 POV 不知）"],
  "hidden_events": ["完全隐藏的事件ID"],
  "pacing": "slow/medium/fast",
  "focus_elements": ["本章重点关注的元素"],
  "scene_transitions": ["场景转换说明"]
}

决策原则：
1. **默认使用主角视角**（primary_pov）— 除非当前剧情有配角独立场景的必要（如主角不在场的关键事件）
2. 隐藏信息可以为后续章节制造悬念
3. 伏笔事件是高级技巧 — 暗示而非明说
4. 节奏应与情节紧张程度匹配
5. 主角视角应占全书 80% 以上，配角视角控制在 20% 以内
6. visible_events + foreshadowing_events + hidden_events 应覆盖全部 event_id，不要遗漏"""


def build_user_prompt(
    plot_structure: dict,
    character_profiles: list[dict],
    chapter_num: int,
    previous_povs: list[str],
    new_events: list[dict] | None = None,
    primary_pov: str = "",
) -> str:
    chars_summary = [
        {"id": c.get("character_id"), "name": c.get("name"), "role": c.get("role")}
        for c in character_profiles
    ]
    pov_hint = ""
    if primary_pov:
        pov_name = next((c["name"] for c in chars_summary if c["id"] == primary_pov), primary_pov)
        pov_hint = f"\n**主视角角色：{pov_name}（{primary_pov}）— 优先使用此角色作为 POV，除非本章有配角独立场景的必要。**\n"

    prompt = f"""第{chapter_num}章的剧情结构：
{json.dumps(plot_structure, ensure_ascii=False, indent=2)}

可选的POV角色：
{json.dumps(chars_summary, ensure_ascii=False, indent=2)}
{pov_hint}
之前章节的POV顺序：{json.dumps(previous_povs, ensure_ascii=False)}
"""

    if new_events:
        events_summary = []
        for e in new_events:
            vis = e.get("visibility", {})
            if isinstance(vis, str):
                vis_desc = f"visibility={vis}"
            else:
                if vis.get("public"):
                    vis_desc = "公开事件"
                else:
                    known = vis.get("known_to", [])
                    vis_desc = f"仅 {', '.join(known)} 知情" if known else "秘密事件"
            events_summary.append({
                "event_id": e.get("event_id", "?"),
                "description": e.get("description", ""),
                "location": e.get("location", ""),
                "actors": e.get("actors", []),
                "visibility": vis_desc,
            })
        prompt += f"""
## 本章新事件（你的 visible/foreshadowing/hidden 必须使用这些 event_id）
{json.dumps(events_summary, ensure_ascii=False, indent=2)}
"""

    prompt += "\n请做出本章的摄影决策。注意可见性规则：POV 不在场且不知情的事件不能放入 visible_events。"
    return prompt

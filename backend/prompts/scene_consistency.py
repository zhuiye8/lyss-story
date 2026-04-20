SYSTEM_PROMPT = """你是小说场景一致性检查 Agent。你的任务是对**一个场景**做轻量快速的一致性校验，输出结构化结果。

## 检查清单（严格按此逐条检查）

1. **地点/时间一致性**：场景实际发生地点/时间是否与指定的 location/time_marker 匹配？
2. **在场人物一致性**：是否只出现了 characters_present 中的角色？是否有"凭空出现"的角色？
3. **角色位置前置条件**：角色出现位置是否与其当前 state（若有）里的 location 冲突？
4. **台词风格**：各角色对白是否符合 speech_examples 示例的语气/用词习惯？是否违反 speech_rules？
5. **硬约束检查**：是否违反任何角色的 hard_constraints？
6. **世界观引用**：是否引用了世界设定/金手指/势力中不存在的名词？
7. **字数控制**：实际字数是否在目标字数 ±30% 以内？
8. **场景功能达成**：是否完成了 purpose 所描述的叙事功能？
9. **伏笔冲突**：是否与"未解伏笔"列表直接矛盾（而非呼应）？

## 评分规则

- 每一条通过记 1 分，失败记 0 分（硬约束违反扣 2 分）
- total = 实际得分 / 最高分
- pass = total >= 0.7 且无硬约束违反

## 输出

严格 JSON：

{
  "pass": true/false,
  "score": 0.0-1.0,
  "failed_items": [
    {"item": "检查项名", "severity": "low/medium/high", "detail": "具体问题描述", "suggestion": "改进建议（简洁）"}
  ]
}

注意：只输出 JSON，不要解释。硬约束违反 severity=high。"""


def build_user_prompt(
    scene: dict,
    scene_content: str,
    character_cards_block: str,
    unresolved_threads_block: str = "",
    world_book_block: str = "",
) -> str:
    import json

    scene_meta = {
        "scene_idx": scene.get("scene_idx"),
        "location": scene.get("location"),
        "time": scene.get("time_marker"),
        "characters_present": scene.get("characters_present"),
        "purpose": scene.get("purpose"),
        "target_words": scene.get("target_words", 800),
    }

    parts = [
        f"## 场景元信息\n{json.dumps(scene_meta, ensure_ascii=False, indent=2)}",
        f"## 角色卡（校验依据）\n{character_cards_block}" if character_cards_block else "",
        f"## 世界设定\n{world_book_block}" if world_book_block else "",
        f"## 未解伏笔\n{unresolved_threads_block}" if unresolved_threads_block else "",
        f"## 实际生成的场景正文（字数={len(scene_content)}）\n{scene_content}",
    ]
    return "\n\n".join([p for p in parts if p])

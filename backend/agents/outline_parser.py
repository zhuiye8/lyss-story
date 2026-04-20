"""Outline parser: rule-based extraction + LLM enrichment.

Step 1: Rule-based split by headings → copies original text verbatim
Step 2: LLM enrichment → fills ONLY empty fields, never modifies existing content
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


def _parse_key_value_block(text: str) -> dict:
    """Parse a block with key: value lines into a dict."""
    result = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(.{1,10})[：:]\s*(.+)$", line)
        if m:
            result[m.group(1).strip()] = m.group(2).strip()
    return result


def _parse_numbered_list(text: str) -> list[str]:
    """Parse numbered or bulleted list items."""
    items = []
    current = ""
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            if current:
                items.append(current)
                current = ""
            continue
        if re.match(r"^[\d]+[.、）)]\s*", line):
            if current:
                items.append(current)
            current = re.sub(r"^[\d]+[.、）)]\s*", "", line)
        elif re.match(r"^[-*·•]\s*", line):
            if current:
                items.append(current)
            current = re.sub(r"^[-*·•]\s*", "", line)
        else:
            current += " " + line if current else line
    if current:
        items.append(current)
    return items


def _build_character(kv: dict, role: str, char_id: str) -> dict:
    return {
        "character_id": char_id,
        "name": kv.get("姓名", kv.get("名字", "")),
        "role": role,
        "gender": kv.get("性别", ""),
        "age": kv.get("年龄", ""),
        "appearance": kv.get("外貌", ""),
        "personality": kv.get("性格", ""),
        "background": kv.get("人物背景", kv.get("背景", "")),
        "goals": [],
        "weaknesses": [],
        "arc_plan": "",
        "relationships": [],
        "status": "active",
    }


def _parse_special_ability(text: str) -> dict:
    """Parse 金手指 section with name/description/functions sub-fields."""
    sa = {"name": "", "description": "", "functions": []}
    lines = text.strip().split("\n")
    current_section = "preamble"
    next_is_name = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # "名称" alone on a line → next non-empty line is the name
        if re.match(r"^名称\s*$", line):
            next_is_name = True
            continue
        if next_is_name:
            sa["name"] = line
            next_is_name = False
            continue

        # "名称：xxx" on same line
        if re.match(r"^名称[：:]", line):
            sa["name"] = re.sub(r"^名称[：:]\s*", "", line).strip()
            continue

        # "功能" heading
        if re.match(r"^功能\s*$", line) or re.match(r"^功能[：:]", line):
            current_section = "functions"
            continue

        # Numbered items → functions
        if re.match(r"^\d+[.、）)]\s*", line):
            func = re.sub(r"^\d+[.、）)]\s*", "", line).strip()
            if func:
                sa["functions"].append(func)
            current_section = "functions"
        elif current_section == "functions" and not re.match(r"^[^\d]", line):
            sa["functions"].append(line)
        else:
            if current_section != "functions":
                if sa["description"]:
                    sa["description"] += "\n" + line
                else:
                    sa["description"] = line

    return sa


def _parse_factions(text: str) -> list[dict]:
    """Parse 势力 section — each faction is 'short title line' + 'description paragraph'."""
    factions = []
    paragraphs = re.split(r"\n\n+", text.strip())

    i = 0
    while i < len(paragraphs):
        para = paragraphs[i].strip()
        i += 1
        if not para:
            continue

        lines = para.split("\n")
        first_line = lines[0].strip()

        # Short first line (< 15 chars) = faction name, rest/next paragraph = description
        if len(first_line) <= 15 and len(lines) == 1:
            name = first_line
            # Next paragraph is the description
            description = ""
            if i < len(paragraphs):
                description = paragraphs[i].strip()
                i += 1
        elif len(first_line) <= 15 and len(lines) > 1:
            name = first_line
            description = "\n".join(lines[1:]).strip()
        else:
            # Long first line — extract name from first clause
            name = first_line.split("，")[0].split(",")[0].split("：")[0][:15].strip()
            description = para

        full = name + " " + description
        stance = "hostile" if any(w in full for w in ["敌", "对抗", "反派", "雇佣", "阴谋", "威胁", "打压"]) else \
                 "allied" if any(w in full for w in ["萧然", "基地", "幸存者", "建立", "发展"]) else "neutral"

        factions.append({"name": name, "description": description, "stance": stance})

    return factions


def _parse_volume(volume_header: str, content: str) -> dict:
    """Parse a single volume section with sub-headings."""
    vol = {
        "volume_num": 1,
        "volume_name": volume_header.strip(),
        "chapter_start": 1,
        "chapter_end": 30,
        "estimated_words": 0,
        "main_plot": "",
        "subplots": [],
        "conflicts": [],
        "new_characters": [],
        "key_locations": [],
        "climax_event": "",
    }

    # Split by sub-headings. Handle both:
    # "主线剧情：xxx" (heading + content on same line)
    # "支线剧情：\n1. xxx" (heading on own line, content below)
    parts = re.split(r"\n?(主线剧情|支线剧情|矛盾冲突)[：:]\s*", content)

    if len(parts) <= 1:
        # No sub-headings found, try alternate split
        parts = re.split(r"\n(主线剧情|支线剧情|矛盾冲突)\s*\n", content)

    if len(parts) <= 1:
        vol["main_plot"] = content.strip()
    else:
        preamble = parts[0].strip()
        if preamble:
            vol["main_plot"] = preamble

        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if "主线" in heading:
                vol["main_plot"] = body
            elif "支线" in heading:
                vol["subplots"] = _parse_numbered_list(body)
            elif "矛盾" in heading or "冲突" in heading:
                vol["conflicts"] = _parse_numbered_list(body)

    return vol


def rule_based_parse(raw_text: str, title_hint: str = "") -> dict:
    """Step 1: Pure rule-based extraction. Copies original text verbatim."""
    lines = raw_text.split("\n")

    # Top-level section detection
    SECTION_HEADS = [
        (r"^世界观$|^世界观背景$|^世界设定$|^背景$", "world_background"),
        (r"^金手指$|^特殊能力$|^外挂$|^异能$", "special_ability"),
        (r"^势力$|^阵营$", "factions"),
        (r"(?:等级|升级|修炼|力量)(?:体系|系统|设定)", "power_system"),
        (r"^主角$|^男主$", "protagonist"),
        (r"^反派$|^大反派$", "antagonist"),
        (r"^配角$|^女主$|^副角$", "supporting_char"),
        (r"^角色$|^人物$|^人设$", "characters_section"),
        (r"第[一二三四五六七八九十\d]+卷", "volume"),
        (r"^剧情大纲$|^剧情$|^大纲$|^故事线$", "plot_section"),
        (r"作品灵感|创作灵感|^灵感$|故事简介|^梗概$", "inspiration"),
    ]

    def detect(line: str) -> str | None:
        s = line.strip().rstrip("：:").strip()
        if not s or len(s) > 40:
            return None
        for pattern, stype in SECTION_HEADS:
            if re.search(pattern, s):
                return stype
        return None

    # Split into sections
    sections: list[tuple[str, str, str]] = []  # (type, heading_line, content)
    current_type = "preamble"
    current_heading = ""
    current_lines: list[str] = []

    for line in lines:
        detected = detect(line)
        if detected:
            if current_lines:
                sections.append((current_type, current_heading, "\n".join(current_lines)))
            current_type = detected
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_type, current_heading, "\n".join(current_lines)))

    logger.info(f"[parser] Detected {len(sections)} sections: {[(s[0], s[1][:20]) for s in sections]}")

    # Build bible
    bible: dict = {
        "bible_version": 2,
        "title": title_hint,
        "genre": "", "tone": "", "one_line_summary": "", "synopsis": "",
        "inspiration": "", "planned_arc": "",
        "world": {
            "world_background": "", "special_ability": None,
            "factions": [], "power_system": None, "world_rules": [],
        },
        "protagonist": None, "antagonist": None, "supporting_characters": [],
        "primary_pov": "char_protagonist",
        "style_guide": {"tone": "", "pov_preference": "第三人称限知", "language_style": "", "dialogue_style": ""},
        "taboos": [], "initial_conflicts": [], "volumes": [],
        "world_rules": [], "power_system": None,
    }

    support_idx = 0
    volume_list: list[dict] = []

    for stype, heading, content in sections:
        content = content.strip()
        if not content:
            continue

        if stype == "world_background":
            bible["world"]["world_background"] = content

        elif stype == "special_ability":
            bible["world"]["special_ability"] = _parse_special_ability(content)

        elif stype == "factions":
            bible["world"]["factions"] = _parse_factions(content)

        elif stype == "protagonist":
            kv = _parse_key_value_block(content)
            bible["protagonist"] = _build_character(kv, "protagonist", "char_protagonist")
            if not bible["protagonist"]["background"]:
                bible["protagonist"]["background"] = content

        elif stype == "antagonist":
            kv = _parse_key_value_block(content)
            bible["antagonist"] = _build_character(kv, "antagonist", "char_antagonist")
            if not bible["antagonist"]["background"]:
                bible["antagonist"]["background"] = content

        elif stype == "supporting_char":
            support_idx += 1
            kv = _parse_key_value_block(content)
            char = _build_character(kv, "supporting", f"char_support_{support_idx}")
            if not char["background"]:
                char["background"] = content
            bible["supporting_characters"].append(char)

        elif stype == "volume":
            vol = _parse_volume(heading, content)
            vol["volume_num"] = len(volume_list) + 1
            volume_list.append(vol)

        elif stype == "plot_section":
            # Check if content contains embedded volumes
            vol_splits = re.split(r"(第[一二三四五六七八九十\d]+卷[^\n]*)", content)
            if len(vol_splits) > 1:
                for i in range(1, len(vol_splits), 2):
                    vol_heading = vol_splits[i].strip()
                    vol_content = vol_splits[i + 1].strip() if i + 1 < len(vol_splits) else ""
                    vol = _parse_volume(vol_heading, vol_content)
                    vol["volume_num"] = len(volume_list) + 1
                    volume_list.append(vol)
            else:
                bible["planned_arc"] = content

        elif stype == "inspiration":
            bible["inspiration"] = content

        elif stype == "preamble":
            if not bible["title"]:
                for line in content.split("\n"):
                    l = line.strip()
                    if l and len(l) < 30:
                        bible["title"] = l
                        break
            if not bible["synopsis"]:
                bible["synopsis"] = content

    # Assign chapter ranges
    bible["volumes"] = volume_list
    ch = 1
    for vol in bible["volumes"]:
        vol["chapter_start"] = ch
        vol["chapter_end"] = ch + 29
        ch = vol["chapter_end"] + 1

    bible["world_rules"] = bible["world"].get("world_rules", [])
    bible["power_system"] = bible["world"].get("power_system")

    logger.info(
        f"[parser] Rule-based result: title={bible['title']}, "
        f"protagonist={'YES' if bible['protagonist'] else 'NO'}, "
        f"factions={len(bible['world']['factions'])}, "
        f"volumes={len(bible['volumes'])}"
    )
    return bible


# ========== Step 2: LLM Enrichment ==========

ENRICH_SYSTEM = """你是小说大纲补全助手。你会收到一份半成品大纲（JSON格式）和用户的原文。

你的任务：只填补 JSON 中为空的字段。**绝不修改已有内容**。

规则：
1. 已有内容（非空字符串、非空数组）→ 原封不动保留，一个字都不改
2. 空字符串 "" → 从原文中推断或提炼填写
3. 空数组 [] → 从原文中提取列表项
4. null → 从原文推断结构化内容

具体补全指引：
- genre: 从原文题材推断（如"末世""玄幻""都市"）
- tone: 从原文基调推断（如"热血""黑暗""轻松"）
- one_line_summary: 从 synopsis 或 inspiration 浓缩为一句话
- synopsis: 从 inspiration 浓缩为 200 字以内
- goals: 从角色背景/性格中提炼核心目标
- weaknesses: 从角色性格中提炼弱点
- arc_plan: 从角色背景推断"初始→发展→终点"弧线

输出完整的 JSON（包含已有内容+你补全的内容）。只输出 JSON。"""

ENRICH_USER = """## 半成品大纲（JSON）
```json
{bible_json}
```

## 用户原文
{raw_text}

请补全 JSON 中所有为空的字段。已有内容不要改动。输出完整 JSON。"""


class OutlineParserAgent:
    """Two-step outline parser: rule extraction + LLM enrichment."""

    name = "outline_parser"

    def __init__(self, llm=None):
        self.llm = llm

    async def run(
        self,
        *,
        raw_text: str,
        title_hint: str = "",
        story_id: str | None = None,
    ) -> dict:
        # Step 1: Rule-based extraction (zero LLM, verbatim copy)
        bible = rule_based_parse(raw_text, title_hint)

        # Step 2: LLM enrichment (fill empty fields only)
        if self.llm:
            try:
                bible = await self._enrich(bible, raw_text, story_id)
            except Exception as e:
                logger.warning(f"[outline_parser] LLM enrichment failed, using rule-based result: {e}")

        return bible

    async def _enrich(self, bible: dict, raw_text: str, story_id: str | None) -> dict:
        """Use LLM to fill empty fields without modifying existing content."""
        from backend.agents.base import BaseAgent

        # Create a temporary agent instance for the LLM call
        class _Enricher(BaseAgent):
            name = "bible_enricher"

        enricher = _Enricher(self.llm)
        bible_json = json.dumps(bible, ensure_ascii=False, indent=2)

        user_prompt = ENRICH_USER.format(
            bible_json=bible_json,
            raw_text=raw_text[:6000],  # Cap to avoid token overflow
        )

        result = await enricher._call_json(
            ENRICH_SYSTEM,
            user_prompt,
            story_id=story_id,
            max_tokens=8192,
            temperature=0.1,  # Very low for minimal creativity
        )

        # Safety: ensure LLM didn't overwrite existing non-empty fields
        result = _protect_existing(bible, result)
        result["bible_version"] = 2
        logger.info("[outline_parser] LLM enrichment complete")
        return result


def _protect_existing(original: dict, enriched: dict) -> dict:
    """Ensure enriched dict never overwrites non-empty fields from original."""
    protected = dict(enriched)
    for key, orig_val in original.items():
        if key == "bible_version":
            continue
        if isinstance(orig_val, str) and orig_val:
            # Original has content → keep it, ignore LLM's version
            protected[key] = orig_val
        elif isinstance(orig_val, list) and orig_val:
            protected[key] = orig_val
        elif isinstance(orig_val, dict) and orig_val:
            # Recurse for nested dicts
            enriched_val = enriched.get(key)
            if isinstance(enriched_val, dict):
                protected[key] = _protect_existing(orig_val, enriched_val)
            else:
                protected[key] = orig_val
    return protected

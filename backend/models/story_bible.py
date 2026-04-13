from pydantic import BaseModel, Field


# ====== V1 models (preserved for backward compatibility) ======

class WorldRule(BaseModel):
    rule_id: str
    description: str


class PowerSystem(BaseModel):
    name: str
    levels: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)


class StyleGuide(BaseModel):
    tone: str = "严肃"
    pov_preference: str = "第三人称限知"
    language_style: str = "现代白话"
    dialogue_style: str = "简洁有力"


class ArcOutline(BaseModel):
    name: str
    chapter_start: int
    chapter_end: int
    goal: str
    key_milestones: list[str] = Field(default_factory=list)


class LongOutline(BaseModel):
    target_chapters: int
    arcs: list[ArcOutline] = Field(default_factory=list)


class StoryBible(BaseModel):
    """V1 StoryBible — kept for backward compat."""
    title: str
    genre: str
    setting: str
    world_rules: list[WorldRule] = Field(default_factory=list)
    power_system: PowerSystem | None = None
    style_guide: StyleGuide = Field(default_factory=StyleGuide)
    taboos: list[str] = Field(default_factory=list)
    initial_conflicts: list[str] = Field(default_factory=list)
    planned_arc: str = ""
    long_outline: LongOutline | None = None


# ====== V2 models ======

class SpecialAbility(BaseModel):
    """金手指"""
    name: str = ""
    description: str = ""
    functions: list[str] = Field(default_factory=list)


class Faction(BaseModel):
    """势力"""
    name: str
    description: str = ""
    stance: str = ""  # "hostile" / "neutral" / "allied"


class CharacterRelationship(BaseModel):
    target_id: str = ""
    target_name: str = ""
    relation_type: str = ""
    description: str = ""


class CharacterProfileV2(BaseModel):
    character_id: str = ""
    name: str
    role: str = "supporting"  # protagonist / antagonist / supporting
    gender: str = ""
    age: str = ""
    appearance: str = ""
    personality: str = ""
    background: str = ""
    goals: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    arc_plan: str = ""  # "起始→发展→终点" 人物弧线
    relationships: list[CharacterRelationship] = Field(default_factory=list)
    status: str = "active"


class VolumeOutline(BaseModel):
    """分卷大纲"""
    volume_num: int = 1
    volume_name: str = ""
    chapter_start: int = 1
    chapter_end: int = 30
    estimated_words: int = 0
    main_plot: str = ""
    subplots: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    new_characters: list[str] = Field(default_factory=list)
    key_locations: list[str] = Field(default_factory=list)
    climax_event: str = ""


class WorldSettingV2(BaseModel):
    world_background: str = ""
    special_ability: SpecialAbility | None = None
    factions: list[Faction] = Field(default_factory=list)
    power_system: PowerSystem | None = None
    world_rules: list[WorldRule] = Field(default_factory=list)


class StoryBibleV2(BaseModel):
    """V2 StoryBible — 对标成熟网文平台大纲结构。"""
    bible_version: int = 2

    # --- 基本信息 ---
    title: str = ""
    genre: str = ""
    tone: str = ""
    one_line_summary: str = ""
    synopsis: str = ""
    inspiration: str = ""

    # --- 世界观 ---
    world: WorldSettingV2 = Field(default_factory=WorldSettingV2)

    # --- 角色（内嵌） ---
    protagonist: CharacterProfileV2 | None = None
    antagonist: CharacterProfileV2 | None = None
    supporting_characters: list[CharacterProfileV2] = Field(default_factory=list)

    # --- 叙事设定 ---
    primary_pov: str = ""  # character_id of default POV
    style_guide: StyleGuide = Field(default_factory=StyleGuide)
    taboos: list[str] = Field(default_factory=list)

    # --- 大纲 ---
    initial_conflicts: list[str] = Field(default_factory=list)
    planned_arc: str = ""
    volumes: list[VolumeOutline] = Field(default_factory=list)

    # --- V1 兼容字段（下游 Agent 直接读这些 key） ---
    setting: str = ""
    world_rules: list[WorldRule] = Field(default_factory=list)
    power_system: PowerSystem | None = None
    long_outline: LongOutline | None = None
    characters: list[dict] = Field(default_factory=list)  # flat list for downstream


def extract_characters_from_bible(bible: dict) -> list[dict]:
    """Extract a flat character list from a V2 bible dict."""
    chars = []
    if bible.get("protagonist"):
        chars.append(bible["protagonist"])
    if bible.get("antagonist"):
        chars.append(bible["antagonist"])
    chars.extend(bible.get("supporting_characters", []))
    # Fallback to V1 flat characters
    if not chars:
        chars = bible.get("characters", [])
    return chars

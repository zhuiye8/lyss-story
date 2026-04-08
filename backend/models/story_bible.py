from pydantic import BaseModel, Field


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


class StoryBible(BaseModel):
    title: str
    genre: str
    setting: str
    world_rules: list[WorldRule] = Field(default_factory=list)
    power_system: PowerSystem | None = None
    style_guide: StyleGuide = Field(default_factory=StyleGuide)
    taboos: list[str] = Field(default_factory=list)
    initial_conflicts: list[str] = Field(default_factory=list)
    planned_arc: str = ""

from datetime import datetime

from pydantic import BaseModel, Field


class ChapterBeat(BaseModel):
    beat_type: str  # 铺垫 / 冲突 / 转折 / 高潮 / 收束
    description: str
    characters_involved: list[str] = Field(default_factory=list)


class PlotStructure(BaseModel):
    chapter_goal: str
    beats: list[ChapterBeat] = Field(default_factory=list)
    key_conflict: str = ""
    emotional_arc: str = ""


class ChapterOutput(BaseModel):
    story_id: str
    chapter_num: int
    title: str = ""
    pov_character_id: str = ""
    content: str = ""
    word_count: int = 0
    events_covered: list[str] = Field(default_factory=list)
    plot_structure: PlotStructure | None = None
    consistency_warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

from pydantic import BaseModel, Field


class Relationship(BaseModel):
    target_id: str
    relation_type: str
    description: str = ""


class CharacterProfile(BaseModel):
    character_id: str
    name: str
    role: str = "supporting"  # protagonist / antagonist / supporting
    personality: str = ""
    background: str = ""
    goals: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    status: str = "active"  # active / inactive / dead


class CharacterMemoryEntry(BaseModel):
    """A single memory extracted from a chapter for a specific character."""
    character_id: str
    chapter_num: int
    category: str = "event"  # event / emotion / relationship / knowledge / decision
    content: str = ""
    emotional_weight: float = 0.5  # 0-1, higher = more important for L1
    related_characters: list[str] = Field(default_factory=list)
    location: str = ""
    visibility: str = "witnessed"  # witnessed / heard / inferred


class RelationshipChange(BaseModel):
    """A relationship change detected from a chapter."""
    subject: str  # character_id
    predicate: str  # e.g. "信任", "怀疑", "知道秘密"
    object: str  # character_id or fact
    detail: str = ""
    change_type: str = "new"  # new / invalidate


class CharacterStateUpdate(BaseModel):
    """Character state snapshot after a chapter."""
    character_id: str
    emotional_state: str = ""
    knowledge_summary: str = ""
    goals_update: str = ""
    status: str = "active"

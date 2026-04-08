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

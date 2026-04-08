from pydantic import BaseModel, Field


class Location(BaseModel):
    location_id: str
    name: str
    description: str = ""
    connected_to: list[str] = Field(default_factory=list)


class WorldState(BaseModel):
    story_id: str
    current_time: int = 0
    time_description: str = "故事开始"
    global_flags: list[str] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)
    active_character_ids: list[str] = Field(default_factory=list)
    version: int = 0

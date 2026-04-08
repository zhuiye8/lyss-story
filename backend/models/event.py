from pydantic import BaseModel, Field


class Event(BaseModel):
    event_id: str
    time: int
    description: str
    actors: list[str] = Field(default_factory=list)
    location: str = ""
    pre_events: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    visibility: str = "full"  # full / partial / hidden
    resolved: bool = False

from pydantic import BaseModel, Field


class CameraDecision(BaseModel):
    pov_character_id: str
    pov_type: str = "第三人称限知"
    visible_events: list[str] = Field(default_factory=list)
    hidden_events: list[str] = Field(default_factory=list)
    pacing: str = "medium"  # slow / medium / fast
    focus_elements: list[str] = Field(default_factory=list)
    scene_transitions: list[str] = Field(default_factory=list)

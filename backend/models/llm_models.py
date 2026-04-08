from datetime import datetime

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    id: str
    display_name: str
    litellm_model: str
    api_key: str = ""
    api_base: str | None = None
    max_tokens: int = 4096
    default_temperature: float = 0.7
    cost_per_million_input: float = 0.0
    cost_per_million_output: float = 0.0
    currency: str = "CNY"  # CNY / USD
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentBinding(BaseModel):
    agent_name: str
    model_config_id: str
    temperature_override: float | None = None
    max_tokens_override: int | None = None


class LLMLogEntry(BaseModel):
    id: int = 0
    story_id: str | None = None
    chapter_num: int | None = None
    agent_name: str = ""
    model_config_id: str = ""
    litellm_model: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    response: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = 0.0
    latency_ms: int = 0
    status: str = "success"
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UsageStats(BaseModel):
    group_key: str
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0

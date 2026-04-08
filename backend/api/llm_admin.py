from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.deps import get_llm_logger, get_model_registry
from backend.llm.logger import LLMLogger
from backend.llm.model_registry import ModelRegistry

router = APIRouter()

VALID_AGENTS = ["director", "world", "planner", "camera", "writer", "consistency"]


# --- Request/Response Models ---

class ModelConfigRequest(BaseModel):
    id: str
    display_name: str
    litellm_model: str
    api_key: str = ""
    api_base: str | None = None
    max_tokens: int = 4096
    default_temperature: float = 0.7
    cost_per_million_input: float = 0.0
    cost_per_million_output: float = 0.0
    currency: str = "CNY"
    is_active: bool = True


class BindAgentRequest(BaseModel):
    model_config_id: str
    temperature_override: float | None = None
    max_tokens_override: int | None = None


# --- Model Config Endpoints ---

@router.get("/models")
async def list_models(registry: ModelRegistry = Depends(get_model_registry)):
    return await registry.list_models()


@router.post("/models")
async def create_model(
    req: ModelConfigRequest,
    registry: ModelRegistry = Depends(get_model_registry),
):
    await registry.save_model(req.model_dump())
    return {"message": "Model created", "id": req.id}


@router.put("/models/{model_id}")
async def update_model(
    model_id: str,
    req: ModelConfigRequest,
    registry: ModelRegistry = Depends(get_model_registry),
):
    existing = await registry.get_model(model_id)
    if not existing:
        raise HTTPException(404, "Model not found")
    data = req.model_dump()
    data["id"] = model_id
    await registry.save_model(data)
    return {"message": "Model updated"}


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    registry: ModelRegistry = Depends(get_model_registry),
):
    await registry.delete_model(model_id)
    return {"message": "Model deleted"}


# --- Agent Binding Endpoints ---

@router.get("/bindings")
async def get_bindings(registry: ModelRegistry = Depends(get_model_registry)):
    bindings = await registry.get_bindings()
    return {"agents": VALID_AGENTS, "bindings": bindings}


@router.put("/bindings/{agent_name}")
async def bind_agent(
    agent_name: str,
    req: BindAgentRequest,
    registry: ModelRegistry = Depends(get_model_registry),
):
    if agent_name not in VALID_AGENTS:
        raise HTTPException(400, f"Invalid agent: {agent_name}")
    model = await registry.get_model(req.model_config_id)
    if not model:
        raise HTTPException(404, "Model config not found")
    await registry.bind_agent(
        agent_name, req.model_config_id,
        req.temperature_override, req.max_tokens_override,
    )
    return {"message": f"Agent '{agent_name}' bound to model '{req.model_config_id}'"}


@router.delete("/bindings/{agent_name}")
async def unbind_agent(
    agent_name: str,
    registry: ModelRegistry = Depends(get_model_registry),
):
    await registry.unbind_agent(agent_name)
    return {"message": f"Agent '{agent_name}' unbound"}


# --- Log Endpoints ---

@router.get("/logs")
async def get_logs(
    agent_name: str | None = None,
    story_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    llm_logger: LLMLogger = Depends(get_llm_logger),
):
    return await llm_logger.get_logs(
        agent_name=agent_name, story_id=story_id,
        status=status, limit=limit, offset=offset,
    )


@router.get("/logs/{log_id}")
async def get_log_detail(
    log_id: int,
    llm_logger: LLMLogger = Depends(get_llm_logger),
):
    log = await llm_logger.get_log_detail(log_id)
    if not log:
        raise HTTPException(404, "Log not found")
    return log


# --- Usage Stats Endpoints ---

@router.get("/usage")
async def get_usage(
    group_by: str = Query(default="agent", regex="^(agent|story|model)$"),
    days: int = Query(default=7, ge=1, le=90),
    llm_logger: LLMLogger = Depends(get_llm_logger),
):
    stats = await llm_logger.get_usage_stats(group_by=group_by, days=days)
    total = await llm_logger.get_total_stats(days=days)
    return {"stats": stats, "total": total}

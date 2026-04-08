from fastapi import Request

from backend.config import Settings
from backend.llm.client import LLMClient
from backend.llm.logger import LLMLogger
from backend.llm.model_registry import ModelRegistry
from backend.progress import ProgressStore
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_sqlite(request: Request) -> SQLiteStore:
    return request.app.state.sqlite


def get_json_store(request: Request) -> JSONStore:
    return request.app.state.json_store


def get_vector(request: Request) -> VectorStore:
    return request.app.state.vector


def get_llm(request: Request) -> LLMClient:
    return request.app.state.llm


def get_model_registry(request: Request) -> ModelRegistry:
    return request.app.state.model_registry


def get_llm_logger(request: Request) -> LLMLogger:
    return request.app.state.llm_logger


def get_progress_store(request: Request) -> ProgressStore:
    return request.app.state.progress_store

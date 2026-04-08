import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import chapters, control, llm_admin, stories
from backend.config import Settings
from backend.llm.client import LLMClient
from backend.llm.logger import LLMLogger
from backend.llm.model_registry import ModelRegistry
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    # Ensure data directories exist
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)

    # Initialize stores
    sqlite = SQLiteStore(settings.sqlite_path)
    await sqlite.initialize()

    # Initialize LLM management
    model_registry = ModelRegistry(settings.sqlite_path)
    llm_logger = LLMLogger(settings.sqlite_path)

    app.state.settings = settings
    app.state.sqlite = sqlite
    app.state.json_store = JSONStore(settings.data_dir)
    app.state.vector = VectorStore(settings.chroma_path)
    app.state.model_registry = model_registry
    app.state.llm_logger = llm_logger
    app.state.llm = LLMClient(settings, registry=model_registry, llm_logger=llm_logger)

    logging.getLogger(__name__).info(
        f"Story Engine started. Default model: {settings.litellm_model}"
    )
    yield


app = FastAPI(title="Story Engine", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(chapters.router, prefix="/api/stories/{story_id}/chapters", tags=["chapters"])
app.include_router(control.router, prefix="/api/stories/{story_id}/control", tags=["control"])
app.include_router(llm_admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}

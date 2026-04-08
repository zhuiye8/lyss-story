import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import chapters, control, stories
from backend.config import Settings
from backend.llm.client import LLMClient
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

    app.state.settings = settings
    app.state.sqlite = sqlite
    app.state.json_store = JSONStore(settings.data_dir)
    app.state.vector = VectorStore(settings.chroma_path)
    app.state.llm = LLMClient(settings)

    logging.getLogger(__name__).info(
        f"Story Engine started. Model: {settings.litellm_model}"
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}

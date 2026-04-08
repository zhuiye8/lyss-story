from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    litellm_model: str = "gpt-4o"
    litellm_api_key: str = ""
    litellm_api_base: str | None = None

    # Storage paths
    sqlite_path: str = "data/story.db"
    checkpoint_db_path: str = "data/checkpoints.db"
    data_dir: str = "data/stories"
    chroma_path: str = "data/chroma"

    # Generation parameters
    max_consistency_retries: int = 3
    default_chapter_word_count: int = 3000

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_prefix": "STORY_"}

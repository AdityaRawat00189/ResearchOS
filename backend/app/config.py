"""
Application configuration and settings.
"""
from pydantic import BaseModel


class ModelRouterConfig(BaseModel):
    """Maps graph node names to Ollama model identifiers."""
    input_init: str = "llama3.1:8b"
    extraction: str = "qwen2.5:7b"
    relevance: str = "qwen2.5:3b"
    outline: str = "llama3.1:8b"
    section_writer: str = "qwen2.5:7b"
    quality_recheck: str = "mistral:7b-instruct"
    validation: str = "mistral:7b-instruct"


class Settings(BaseModel):
    """Global application settings."""
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 120
    model_router: ModelRouterConfig = ModelRouterConfig()

    max_relevance_retries: int = 3
    max_writing_retries_per_section: int = 2
    max_validation_retries: int = 2
    recursion_limit: int = 100

    words_per_page: int = 450
    min_relevance_score: float = 0.5
    min_quality_score: float = 0.6
    min_kept_chunks: int = 5

    output_dir: str = "outputs"

    max_search_results_per_query: int = 3


settings = Settings()

"""Central configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
EVAL_DIR = PROJECT_ROOT / "evaluation_results"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8-sig",   # handles BOM produced by Windows editors
        extra="ignore",
    )

    # --- API ---
    openrouter_api_key: str = ""
    openrouter_site_url: str = "http://localhost:8501"
    openrouter_app_name: str = "College FAQ Chatbot"

    # --- Branding (make the app your own) ---
    institution_name: str = "Your College"
    app_title: str = "College FAQ Chatbot"
    app_icon: str = "🎓"
    knowledge_base_label: str = "knowledge_base.docx"

    # --- Models ---
    llm_model: str = "openai/gpt-4o-mini"
    embedding_model: str = "openai/text-embedding-3-small"

    # --- Embedding backend ---
    # "openai" -> OpenAI-compatible embeddings endpoint (OpenRouter)
    # "local"  -> local ONNX model via fastembed (no API key needed)
    embedding_provider: str = "openai"
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"

    # --- Paths ---
    knowledge_base_path: Path = DATA_DIR / "knowledge_base.docx"
    chroma_persist_dir: Path = CHROMA_DIR
    collection_name: str = "college_knowledge_base"

    # --- Retrieval core ---
    retrieval_top_k: int = 5
    relevance_score_threshold: float = 0.20

    # --- MMR settings ---
    fetch_k: int = 20           # candidates fetched before MMR diversity pass
    lambda_mult: float = 0.5    # MMR: 0=max diversity, 1=max relevance

    # --- Adaptive-k ---
    adaptive_k_threshold: float = 0.45  # if best score < this, expand to fetch_k

    # --- Chunking ---
    chunk_size: int = 500
    chunk_overlap: int = 100

    # --- Query pipeline ---
    enable_query_rewriting: bool = True

    # --- OpenRouter base ---
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    @property
    def openrouter_headers(self) -> dict[str, str]:
        return {
            "HTTP-Referer": self.openrouter_site_url,
            "X-Title": self.openrouter_app_name,
        }


def get_settings() -> Settings:
    return Settings()

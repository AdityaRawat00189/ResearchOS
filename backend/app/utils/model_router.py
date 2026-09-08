"""
Model router — maps graph node names to Ollama model identifiers.
Centralises model selection so you can A/B test different models
without touching any node logic.
"""
from app.config import settings


class ModelRouter:
    """Resolve the Ollama model name for a given graph node."""

    def __init__(self):
        cfg = settings.model_router
        self._mapping: dict[str, str] = {
            "input_init": cfg.input_init,
            "extraction": cfg.extraction,
            "relevance": cfg.relevance,
            "outline": cfg.outline,
            "section_writer": cfg.section_writer,
            "quality_recheck": cfg.quality_recheck,
            "validation": cfg.validation,
        }

    def get_model(self, node_name: str) -> str:
        """Return the model identifier for *node_name*.

        Raises KeyError if the node is not registered.
        """
        if node_name not in self._mapping:
            raise KeyError(
                f"No model configured for node '{node_name}'. "
                f"Available: {list(self._mapping.keys())}"
            )
        return self._mapping[node_name]

    def set_model(self, node_name: str, model_name: str) -> None:
        """Override the model for a specific node at runtime."""
        self._mapping[node_name] = model_name

    def list_models(self) -> dict[str, str]:
        """Return a copy of the full node → model mapping."""
        return dict(self._mapping)


model_router = ModelRouter()

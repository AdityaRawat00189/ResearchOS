"""
Wrapper around langchain_ollama.ChatOllama with timeout, retry,
and model-name passthrough from the ModelRouter.
"""
import logging
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.config import settings
from app.utils.model_router import model_router

logger = logging.getLogger(__name__)


def get_llm(node_name: str, temperature: float = 0.3,
            max_tokens: int = 2048) -> ChatOllama:
    """Return a ChatOllama instance configured for the given node.

    Parameters
    ----------
    node_name : str
        Graph node name (looked up in ModelRouter).
    temperature : float
        Sampling temperature.
    max_tokens : int
        Maximum output tokens (num_predict).
    """
    model_name = model_router.get_model(node_name)
    logger.info("Node '%s' → model '%s'", node_name, model_name)
    return ChatOllama(
        model=model_name,
        base_url=settings.ollama_base_url,
        temperature=temperature,
        num_predict=max_tokens,
        timeout=settings.ollama_timeout,
    )


def invoke_llm(node_name: str, messages: list[BaseMessage],
               temperature: float = 0.3, max_tokens: int = 2048) -> str:
    """Convenience: invoke an LLM for *node_name* and return the text content.

    Handles retries on connection errors (up to 2 attempts).
    """
    llm = get_llm(node_name, temperature=temperature, max_tokens=max_tokens)
    last_err = None
    for attempt in range(3):
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as exc:
            last_err = exc
            logger.warning("LLM call attempt %d failed for node '%s': %s",
                           attempt + 1, node_name, exc)
    raise RuntimeError(
        f"LLM call failed after 3 attempts for node '{node_name}': {last_err}"
    )


def invoke_llm_json(node_name: str, messages: list[BaseMessage],
                     temperature: float = 0.1, max_tokens: int = 1024) -> str:
    """Invoke LLM with JSON output format hint.

    Adds a system instruction to respond in JSON and uses low temperature.
    Returns raw string — caller is responsible for parsing.
    """
    json_instruction = SystemMessage(
        content="You MUST respond with valid JSON only. No markdown fences, no extra text."
    )
    all_messages = [json_instruction] + list(messages)
    return invoke_llm(node_name, all_messages,
                      temperature=temperature, max_tokens=max_tokens)

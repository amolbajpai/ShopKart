from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.ai.llm.base import BaseLLMProvider, LLMConfigError
from app.config import get_settings


def require_openrouter_key() -> str:
    key = (get_settings().openrouter_api_key or "").strip()
    if not key:
        raise LLMConfigError("OPENROUTER_API_KEY is not set")
    return key


class OpenRouterLLM(BaseLLMProvider):
    name = "openrouter"

    def build(self, *, temperature: float) -> BaseChatModel:
        config = get_settings()
        return ChatOpenAI(
            model=config.openrouter_model or "openrouter/free",
            api_key=require_openrouter_key(),
            base_url=config.openrouter_base_url or "https://openrouter.ai/api/v1",
            temperature=temperature,
        )

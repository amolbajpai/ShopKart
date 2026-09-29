from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.ai.llm.base import BaseLLMProvider, LLMConfigError
from app.config import settings


class GrokLLM(BaseLLMProvider):
    name = "grok"

    def build(self, *, temperature: float) -> BaseChatModel:
        if not settings.grok_api_key:
            raise LLMConfigError("GROK_API_KEY is not set")
        return ChatOpenAI(
            model=settings.grok_model or "grok-3-mini",
            api_key=settings.grok_api_key,
            base_url=settings.grok_base_url or "https://api.x.ai/v1",
            temperature=temperature,
        )

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.ai.llm.base import BaseLLMProvider, LLMConfigError
from app.config import settings


class OpenAILLM(BaseLLMProvider):
    name = "openai"

    def build(self, *, temperature: float) -> BaseChatModel:
        if not settings.openai_api_key:
            raise LLMConfigError("OPENAI_API_KEY is not set")
        return ChatOpenAI(
            model=settings.openai_model or "gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=temperature,
        )

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_anthropic import ChatAnthropic

from app.ai.llm.base import BaseLLMProvider, LLMConfigError
from app.config import settings


class AnthropicLLM(BaseLLMProvider):
    name = "anthropic"

    def build(self, *, temperature: float) -> BaseChatModel:
        if not settings.anthropic_api_key:
            raise LLMConfigError("ANTHROPIC_API_KEY is not set")
        return ChatAnthropic(
            model=settings.anthropic_model or "claude-sonnet-4-0",
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )

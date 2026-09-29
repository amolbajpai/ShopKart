from langchain_core.language_models.chat_models import BaseChatModel

from app.ai.llm.anthropic import AnthropicLLM
from app.ai.llm.base import BaseLLMProvider, LLMConfigError
from app.ai.llm.gemini import GeminiLLM
from app.ai.llm.grok import GrokLLM
from app.ai.llm.openrouter import OpenRouterLLM
from app.ai.llm.openai import OpenAILLM
from app.config import get_settings


class LLMFactory:
    """Build any supported chat model from config or an explicit provider name."""

    _registry: dict[str, type[BaseLLMProvider]] = {
        GeminiLLM.name: GeminiLLM,
        OpenAILLM.name: OpenAILLM,
        AnthropicLLM.name: AnthropicLLM,
        GrokLLM.name: GrokLLM,
        OpenRouterLLM.name: OpenRouterLLM,
    }

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)

    @classmethod
    def create(
        cls,
        provider: str | None = None,
        *,
        temperature: float | None = None,
    ) -> BaseChatModel:
        config = get_settings()
        name = (provider or config.llm_provider or "gemini").strip().lower()
        impl = cls._registry.get(name)
        if impl is None:
            raise LLMConfigError(
                f"Unknown LLM provider '{name}'. Use one of: {', '.join(cls.available())}"
            )
        temp = config.llm_temperature if temperature is None else temperature
        return impl().build(temperature=temp)

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.ai.llm.base import BaseLLMProvider, LLMConfigError
from app.config import get_settings


class GeminiLLM(BaseLLMProvider):
    name = "gemini"

    def build(self, *, temperature: float) -> BaseChatModel:
        config = get_settings()
        if not config.google_api_key:
            raise LLMConfigError("GOOGLE_API_KEY is not set")
        return ChatGoogleGenerativeAI(
            model=config.gemini_model or "gemini-2.0-flash",
            google_api_key=config.google_api_key,
            temperature=temperature,
            max_retries=1,
        )

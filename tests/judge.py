from deepeval.models.base_model import DeepEvalBaseLLM

from app.config import get_settings


def build_judge() -> DeepEvalBaseLLM | None:
    """Judge model for DeepEval metrics. Prefers OpenRouter, then OpenAI, then Gemini."""
    config = get_settings()
    if config.openrouter_api_key:
        from deepeval.models import OpenRouterModel

        return OpenRouterModel(
            model=config.openrouter_model or "openrouter/free",
            api_key=config.openrouter_api_key,
            base_url=config.openrouter_base_url or "https://openrouter.ai/api/v1",
            temperature=0,
        )
    if config.openai_api_key:
        from deepeval.models import OpenAIModel

        return OpenAIModel(model=config.openai_model or "gpt-4o-mini", api_key=config.openai_api_key)
    if config.google_api_key:
        from deepeval.models import GeminiModel

        return GeminiModel(model=config.gemini_model or "gemini-2.0-flash", api_key=config.google_api_key)
    return None

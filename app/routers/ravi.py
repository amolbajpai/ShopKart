from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.llm.base import LLMConfigError
from app.ai.llm.factory import LLMFactory
from app.ai.service import ask_ravi
from app.config import get_settings

router = APIRouter(prefix="/api/ravi", tags=["ravi"])


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)


class ChatOut(BaseModel):
    reply: str
    assistant: str = "Ravi"


@router.get("/status")
def status():
    config = get_settings()
    return {
        "name": "Ravi AI Assistant",
        "provider": config.llm_provider,
        "model": _active_model(config),
        "providers": LLMFactory.available(),
        "ready": _provider_ready(),
    }


@router.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn):
    if not _provider_ready():
        raise HTTPException(
            status_code=503,
            detail="Ravi is not configured. Set the API key for LLM_PROVIDER in .env.",
        )
    try:
        reply = ask_ravi(payload.message, [t.model_dump() for t in payload.history])
    except LLMConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_public_error(exc)) from exc
    return ChatOut(reply=reply)


def _public_error(exc: Exception) -> str:
    text = str(exc)
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return (
            "Gemini quota is used up for this model. Wait a minute and try again, "
            "or set GEMINI_MODEL in .env to another model (for example gemini-2.0-flash)."
        )
    return f"Ravi could not answer: {text}"


def _active_model(config) -> str:
    models = {
        "gemini": config.gemini_model,
        "openai": config.openai_model,
        "anthropic": config.anthropic_model,
        "grok": config.grok_model,
        "openrouter": config.openrouter_model,
    }
    return models.get((config.llm_provider or "gemini").lower(), "")


def _provider_ready() -> bool:
    config = get_settings()
    name = (config.llm_provider or "gemini").lower()
    keys = {
        "gemini": config.google_api_key,
        "openai": config.openai_api_key,
        "anthropic": config.anthropic_api_key,
        "grok": config.grok_api_key,
        "openrouter": config.openrouter_api_key,
    }
    return bool(keys.get(name))

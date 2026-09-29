from abc import ABC, abstractmethod

from langchain_core.language_models.chat_models import BaseChatModel


class LLMConfigError(ValueError):
    """Raised when a provider is unknown or its API key / model is missing."""


class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    def build(self, *, temperature: float) -> BaseChatModel:
        raise NotImplementedError

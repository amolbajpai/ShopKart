from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ShopKart"
    secret_key: str = "dev-secret-change-me-in-production"
    database_url: str = "sqlite:///./shopkart.db"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    oauth_redirect_base: str = "http://127.0.0.1:8000"
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    llm_provider: str = "gemini"
    llm_temperature: float = 0.3
    llm_call_gap_seconds: float = 6.0
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-0"
    grok_api_key: str = ""
    grok_model: str = "grok-3-mini"
    grok_base_url: str = "https://api.x.ai/v1"
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"


settings = Settings()


def get_settings() -> Settings:
    """Re-read .env so LLM keys/models pick up without a full process restart."""
    return Settings()

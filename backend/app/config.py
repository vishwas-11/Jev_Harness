from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    supabase_db_url: str | None = None
    ai_gateway_api_key: str | None = None
    ai_gateway_base_url: str = "https://ai-gateway.vercel.sh/typesafe"
    typesafe_api_key: str | None = None
    jev_model: str = "typesafe-ai/jev"
    jev_timeout: float = 30.0
    llm_api_key: str | None = None
    llm_provider: str = "gemini"
    llm_model: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def has_jev_credentials(self) -> bool:
        return bool(self.ai_gateway_api_key or self.typesafe_api_key)

    @property
    def effective_jev_api_key(self) -> str | None:
        return self.ai_gateway_api_key or self.typesafe_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()


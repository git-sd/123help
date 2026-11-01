from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    allowed_origins: str = "http://localhost:5173"
    supabase_url: str = ""
    supabase_jwks_url: str = ""
    supabase_service_role_key: str = ""
    tinyfish_api_key: str = ""
    gemini_api_key: str = ""
    resend_api_key: str = ""
    from_email: str = ""
    max_concurrent_investigations: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

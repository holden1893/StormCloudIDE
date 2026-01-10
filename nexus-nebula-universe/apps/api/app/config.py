from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    web_origin: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    supabase_url: AnyHttpUrl
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_artifacts_bucket: str = "nexus-nebula-artifacts"

    # Provider keys (optional; graph will fallback)
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    google_api_key: str | None = None
    ollama_base_url: str | None = "http://127.0.0.1:11434"

    # Preferred models (overrideable)
    model_groq: str = "groq/llama3-70b-8192"
    model_openrouter_claude: str = "openrouter/anthropic/claude-3.5-sonnet"
    model_openrouter_gpt4o: str = "openrouter/openai/gpt-4o"
    model_gemini: str = "gemini/gemini-1.5-pro"
    model_ollama: str = "ollama/llama3:8b"
    model_image_flux: str = "openrouter/black-forest-labs/flux-1.1-pro"

    # Basic rate limiting (in-memory)
    rate_limit_rpm: int = Field(default=20, description="requests per minute per IP")

    # Stripe (stub-ready)
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    public_app_url: str = "http://localhost:3000"


settings = Settings()

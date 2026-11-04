from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    openai_api_key: str
    cors_origins: str = "http://localhost:5173"
    chat_model: str = "gpt-4o-mini"   # המודל שמנסח תשובות
    web_model: str = "gpt-4o-mini"    # המודל שמבצע חיפוש אינטרנט
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
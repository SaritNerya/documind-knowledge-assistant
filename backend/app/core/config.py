from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    openai_api_key: str
    cors_origins: str = "http://localhost:5173"
    chat_model: str = "gpt-4o-mini"   # המודל שמנסח תשובות
    web_model: str = "gpt-4o-mini"    # המודל שמבצע חיפוש אינטרנט
    model_config = SettingsConfigDict(env_file=".env")
    invite_code: str = ""            # אם ריק, כל אחד יכול להירשם
    max_docs_per_user: int = 10
    max_upload_mb: int = 5
    daily_question_limit: int = 30


settings = Settings()
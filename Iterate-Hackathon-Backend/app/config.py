# app/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")

    mongodb_uri: str = Field(..., env="MONGODB_URI")
    mongodb_db_name: str = Field("chat_history", env="MONGODB_DB_NAME")
    mongodb_collection_name: str = Field("message_store", env="MONGODB_COLLECTION_NAME")

    claude_model: str = Field(
        "claude-3-5-sonnet-20241022",
        env="CLAUDE_MODEL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

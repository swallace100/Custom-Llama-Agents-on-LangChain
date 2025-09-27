from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # App
    port: int = Field(8080, env="PORT")
    log_level: str = Field("info", env="LOG_LEVEL")

    # Models / APIs
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    llama_server_url: str = Field("http://localhost:8000", env="LLAMA_SERVER_URL")
    embeddings_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDINGS_MODEL"
    )

    # Databases
    postgres_user: Optional[str] = Field(None, env="POSTGRES_USER")
    postgres_password: Optional[str] = Field(None, env="POSTGRES_PASSWORD")
    postgres_db: Optional[str] = Field(None, env="POSTGRES_DB")
    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")

    mongo_user: Optional[str] = Field(None, env="MONGO_INITDB_ROOT_USERNAME")
    mongo_password: Optional[str] = Field(None, env="MONGO_INITDB_ROOT_PASSWORD")
    mongo_host: str = Field("localhost", env="MONGO_HOST")
    mongo_port: int = Field(27017, env="MONGO_PORT")

    # GitHub
    github_token: Optional[str] = Field(None, env="GITHUB_TOKEN")

    # Environment
    env: str = Field("development", env="ENV")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# singleton for app-wide use
settings = Settings()

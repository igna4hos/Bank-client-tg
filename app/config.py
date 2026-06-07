from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    backend_url: str = "http://bank-backend:8000"

    model_config = {"env_file": ".env"}


settings = Settings()

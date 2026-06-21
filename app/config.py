from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    backend_url: str = "http://bank-backend:8000"

    yandex_folder_id: str
    yandex_api_key: str
    yandex_model: str = "yandexgpt-5.1/latest"

    model_config = {"env_file": ".env"}


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8420
    log_level: str = "info"

    model_config = {"env_prefix": "PRISM_"}


settings = Settings()

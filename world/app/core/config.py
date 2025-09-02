from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str
    POSTGRES_USER: str = "petri_user"
    POSTGRES_PASSWORD: str = "petri_password"
    POSTGRES_DB: str = "petri_world"

    # API Configuration
    API_KEY: str

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()

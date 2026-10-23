from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise Salesforce AI Support Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # API Configurations
    API_V1_PREFIX: str = "/api/v1"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # LLM Settings (supports OpenAI, Gemini, Azure OpenAI or local mock)
    OPENAI_API_KEY: Optional[str] = "sk-enterprise-mock-key"
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1

    # Salesforce Integration
    SALESFORCE_INSTANCE_URL: str = "https://enterprise-cloudops.my.salesforce.com"
    SALESFORCE_CLIENT_ID: Optional[str] = "mock_sf_client_id"
    SALESFORCE_CLIENT_SECRET: Optional[str] = "mock_sf_client_secret"
    SALESFORCE_API_VERSION: str = "v58.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

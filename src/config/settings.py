from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    telegram_bot_token: str = ""
    telegram_allowed_user_ids: str = ""
    olx_base_url: str = "https://www.olx.pt"
    facebook_marketplace_url: str = "https://www.facebook.com/marketplace"
    user_agent: str = "Mozilla/5.0"
    request_timeout_seconds: int = 30
    scrape_max_pages: int = 5
    min_margin: float = 0.2
    max_listing_price: float = 1200.0
    db_url: str = "sqlite:///./data/gpu_flip.db"
    price_comp_urls: str = ""
    healthchecks_enabled: bool = True

    class Config:
        env_file = ".env"


settings = Settings()

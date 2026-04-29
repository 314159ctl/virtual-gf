"""应用配置 - Pydantic Settings 从环境变量加载"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DeepSeek API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_token: int = 2000
    deepseek_temperature: float = 0.9

    # 绘画 API (豆包 Seedream)
    painting_enabled: bool = True
    painting_api_key: str = ""
    painting_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    painting_model: str = "doubao-seedream-4-5-251128"

    # 数据库
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/virtual_gf"
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # TTS
    tts_voice: str = "zh-CN-XiaoxiaoNeural"

    # App
    app_port: int = 8000
    debug: bool = False
    cors_origins: str = "http://localhost:5173"

    # 配额
    free_daily_messages: int = 50
    free_daily_images: int = 3
    premium_daily_messages: int = 500
    premium_daily_images: int = 50

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

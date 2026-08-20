from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    public_base_url: str = "https://kothakhata.app"
    jwt_secret_key: str = "kothakhata_jwt_secure_secret_key_2026"
    admin_password: str = "admin"

    database_url: str = "postgresql+asyncpg://aisathi:aisathi@localhost:5432/aisathi"

    sarvam_api_key: str = ""
    sarvam_base_url: str = "https://api.sarvam.ai"
    sarvam_chat_model: str = "sarvam-105b"
    sarvam_advanced_model: str = "sarvam-105b"
    sarvam_conversational_model: str = "sarvam-105b-conversations"
    sarvam_translation_model: str = "mayura:v1"
    sarvam_vision_model: str = "Vision"
    sarvam_parse_model: str = "Parse"

    saaras_model: str = "saaras:v4"
    saaras_fallback_model: str = "saaras:v3"
    routine_confidence_floor: float = 0.80

    whisper_model_path: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    flux_api_key: str = ""
    flux_base_url: str = "https://api.bfl.ml"

    azure_storage_connection_string: str = ""
    azure_storage_container: str = "aisathi-assets"

    data_gov_in_api_key: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    debug: bool = False
    session_ttl_seconds: int = 1800
    max_messages_per_hour: int = 30
    max_text_message_chars: int = 2000

    bengali_font_path: str = "assets/fonts/NotoSansBengali-Bold.ttf"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    metrics_alert_email: str = ""
    admin_api_token: str = ""

    webhook_secret: str = "default_webhook_secret"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

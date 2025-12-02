from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./tone_decoder.db"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    allowed_extensions: str = ".wav"
    frequency_tolerance_hz: float = 2.0

    # Audio processing parameters
    sample_rate: int = 44100
    tone1_duration: float = 1.0  # First tone ~1 second
    tone2_duration: float = 3.0  # Second tone ~3 seconds
    min_tone_gap: float = 0.0    # No gap between tones
    max_tone_gap: float = 0.5    # Max gap to still consider sequential

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

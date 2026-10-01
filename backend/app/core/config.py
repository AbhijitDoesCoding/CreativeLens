import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "CreativeLens"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "campaigns"
    
    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", f"sqlite:///{self.DATA_DIR}/creative_lens.db")

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

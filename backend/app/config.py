import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in project root or backend folder
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent

env_path_root = ROOT_DIR / ".env"
env_path_backend = BACKEND_DIR / ".env"

if env_path_root.exists():
    load_dotenv(env_path_root)
elif env_path_backend.exists():
    load_dotenv(env_path_backend)
else:
    load_dotenv()

class Settings:
    def __init__(self):
        self.reload_from_env()

    def reload_from_env(self):
        if env_path_root.exists():
            load_dotenv(env_path_root, override=True)
        elif env_path_backend.exists():
            load_dotenv(env_path_backend, override=True)
        else:
            load_dotenv(override=True)

        self.PROJECT_NAME: str = "AI News Monitor & Daily Digest"
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
        
        self.TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        
        # Scheduled digest times (24h format: "HH:MM")
        self.DIGEST_TIMES: list[str] = ["10:00", "14:00", "21:00"]
        self.FETCH_INTERVAL_MINUTES: int = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))
        self.TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Dhaka")
        
        # Email Digest Configuration (100% Free SMTP / Gmail App Password)
        self.EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() in ("true", "1", "yes")
        self.EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com").strip()
        self.EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
        self.EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "").strip()
        self.EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "").strip()
        self.EMAIL_RECIPIENT: str = os.getenv("EMAIL_RECIPIENT", "").strip()

        # Fallback: if username is missing but recipient is set (or vice versa), auto-link
        if not self.EMAIL_USERNAME and self.EMAIL_RECIPIENT:
            self.EMAIL_USERNAME = self.EMAIL_RECIPIENT
        if not self.EMAIL_RECIPIENT and self.EMAIL_USERNAME:
            self.EMAIL_RECIPIENT = self.EMAIL_USERNAME

        self.DB_PATH: Path = BACKEND_DIR / "news.db"
        self.HOST: str = os.getenv("HOST", "127.0.0.1")
        self.PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()


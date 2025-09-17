import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
	telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
	gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
	database_url: str = os.getenv("DATABASE_URL", "")
	app_tz: str = os.getenv("APP_TZ", "Europe/Moscow")
	run_mode: str = os.getenv("RUN_MODE", "polling")  # polling|webhook
	public_url: str = os.getenv("PUBLIC_URL", "")


settings = Settings()


def validate_settings() -> None:
	missing: list[str] = []
	if not settings.telegram_bot_token:
		missing.append("TELEGRAM_BOT_TOKEN")
	if not settings.gemini_api_key:
		missing.append("GEMINI_API_KEY")
	if not settings.database_url:
		missing.append("DATABASE_URL")
	if settings.run_mode == "webhook" and not settings.public_url:
		missing.append("PUBLIC_URL (for webhook mode)")
	if missing:
		raise RuntimeError(
			"Missing required environment variables: " + ", ".join(missing)
		)
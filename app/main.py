import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from .config import settings, validate_settings


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


aio_bot: Bot | None = None

dp = Dispatcher()


@dp.message(Command("start", "help"))
async def cmd_help(message: Message) -> None:
	text = (
		"Я считаю траты в этом чате. Пиши: <сумма> [категория] [описание].\n"
		"Категории: alcohol | smokes | fun | restaurants.\n"
		"Команды: /week /month /all /stats /undo /help\n"
		"Просто число — засчитаю как alcohol."
	)
	await message.reply(text)


@dp.message(F.text.regexp(r"^(?=.*\d)"))
async def handle_freeform_expense(message: Message) -> None:
	# Placeholder: just echo for now; will replace with real parsing + DB
	await message.reply("Принял! Сохраню после настройки базы. Напиши /help для формата.")


async def run_polling() -> None:
	global aio_bot
	aio_bot = Bot(token=settings.telegram_bot_token)
	logger.info("Starting bot in long-polling mode")
	await dp.start_polling(aio_bot, allowed_updates=dp.resolve_used_update_types())


try:
	from fastapi import FastAPI, Request
except Exception:
	FastAPI = None  # type: ignore


def build_fastapi_app() -> "FastAPI":
	from fastapi import FastAPI

	app = FastAPI()

	@asynccontextmanager
	async def lifespan(_app: "FastAPI"):
		nonlocal aio_bot
		aio_bot = Bot(token=settings.telegram_bot_token)
		yield
		if aio_bot is not None:
			await aio_bot.session.close()

	app.router.lifespan_context = lifespan  # type: ignore[attr-defined]

	@app.post("/webhook")
	async def telegram_webhook(request: Request):  # type: ignore[no-redef]
		update = await request.json()
		await dp.feed_update(aio_bot, update)  # type: ignore[arg-type]
		return {"ok": True}

	@app.get("/")
	async def root():
		return {"ok": True}

	return app


if __name__ == "__main__":
	validate_settings()
	if settings.run_mode == "webhook":
		if FastAPI is None:
			raise RuntimeError("FastAPI is not available. Switch RUN_MODE to polling.")
		import uvicorn

		app = build_fastapi_app()
		uvicorn.run(app, host="0.0.0.0", port=8080)
	else:
		asyncio.run(run_polling())
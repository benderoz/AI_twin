import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from .config import settings, validate_settings
from .db import init_db, get_sessionmaker, ensure_user_and_chat, add_expense, totals_for_range, month_bounds, delete_last_user_expense
from .utils.parsing import parse_expense
from .services.gemini import generate_dark_humor_line


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


aio_bot: Bot | None = None

dp = Dispatcher()


@dp.message(Command("start", "help"))
async def cmd_help(message: Message) -> None:
	text = (
		"Я считаю траты в этом чате. Пиши: <сумма> [категория] [описание].\n"
		"Категории: alcohol | smokes | fun | restaurants and bars.\n"
		"Команды: /week /month /all /stats /undo /help\n"
		"Просто число — засчитаю как alcohol."
	)
	await message.reply(text)


def _now_utc() -> datetime:
	return datetime.now(timezone.utc)


@dp.message(F.text.regexp(r"^(?=.*\d)"))
async def handle_freeform_expense(message: Message) -> None:
	parsed = parse_expense(message.text or "")
	if not parsed:
		await message.reply("Не смог распознать сумму. Пример: 1200 алкоголь вино.")
		return

	Session = get_sessionmaker()
	async with Session() as session:
		user, chat = await ensure_user_and_chat(
			session,
			tg_user_id=message.from_user.id,
			username=message.from_user.username,
			tg_chat_id=message.chat.id,
			chat_title=message.chat.title,
		)
		await add_expense(session, chat, user, parsed.amount, parsed.category, parsed.description)
		await session.commit()

		# Monthly total
		now = _now_utc()
		start, end = month_bounds(now)
		totals = await totals_for_range(session, chat, start, end)

	line = generate_dark_humor_line(parsed.amount, parsed.category, totals.sum_total)

	desc_part = f" — {parsed.description}" if parsed.description else ""
	await message.reply(
		f"Записал: {parsed.amount:.2f} ₽, {parsed.category}{desc_part}.\n"
		f"В этом месяце всего: {totals.sum_total:.2f} ₽.\n"
		f"{line}"
	)


async def _stats_reply(message: Message, since: datetime | None, until: datetime | None, title: str) -> None:
	Session = get_sessionmaker()
	async with Session() as session:
		_, chat = await ensure_user_and_chat(
			session,
			tg_user_id=message.from_user.id,
			username=message.from_user.username,
			tg_chat_id=message.chat.id,
			chat_title=message.chat.title,
		)
		totals = await totals_for_range(session, chat, since, until)

	lines = [f"{title}: {totals.sum_total:.2f} ₽"]
	if totals.by_user:
		lines.append("По людям:")
		for username, s in totals.by_user:
			lines.append(f"- {username}: {s:.2f} ₽")
	if totals.by_category:
		lines.append("По категориям:")
		for cat, s in totals.by_category:
			lines.append(f"- {cat}: {s:.2f} ₽")
	await message.reply("\n".join(lines))


@dp.message(Command("week"))
async def cmd_week(message: Message) -> None:
	now = _now_utc()
	since = now - timedelta(days=7)
	await _stats_reply(message, since, now, "За 7 дней")


@dp.message(Command("month"))
async def cmd_month(message: Message) -> None:
	now = _now_utc()
	since, until = month_bounds(now)
	await _stats_reply(message, since, until, "За месяц")


@dp.message(Command("all"))
async def cmd_all(message: Message) -> None:
	await _stats_reply(message, None, None, "За всё время")


@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
	now = _now_utc()
	since, until = month_bounds(now)
	await _stats_reply(message, since, until, "Сводка (месяц)")


@dp.message(Command("undo"))
async def cmd_undo(message: Message) -> None:
	Session = get_sessionmaker()
	async with Session() as session:
		user, chat = await ensure_user_and_chat(
			session,
			tg_user_id=message.from_user.id,
			username=message.from_user.username,
			tg_chat_id=message.chat.id,
			chat_title=message.chat.title,
		)
		last = await delete_last_user_expense(session, chat, user)
		await session.commit()
		if last is None:
			await message.reply("Нет записей для удаления.")
			return
		await message.reply(f"Удалено: {last.amount} ₽, {last.category}.")


async def run_polling() -> None:
	global aio_bot
	aio_bot = Bot(token=settings.telegram_bot_token)
	logger.info("Initializing database schema (if needed)")
	await init_db()
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
		await init_db()
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
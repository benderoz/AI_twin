from __future__ import annotations

import asyncio
import ssl
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence, Tuple

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .config import settings


# --- SQLAlchemy setup ---

class Base(DeclarativeBase):
	pass


def _to_asyncpg_url(url: str) -> str:
	if url.startswith("postgresql+asyncpg://"):
		return url
	if url.startswith("postgresql://"):
		return url.replace("postgresql://", "postgresql+asyncpg://", 1)
	return url


_engine: AsyncEngine | None = None
_Session: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
	global _engine, _Session
	if _engine is None:
		# Force SSL for Supabase/managed Postgres (safe for most hosts)
		connect_args = {"ssl": True}
		_engine = create_async_engine(
			_to_asyncpg_url(settings.database_url), echo=False, pool_pre_ping=True, connect_args=connect_args
		)
		_Session = async_sessionmaker(_engine, expire_on_commit=False)
	return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
	global _Session
	if _Session is None:
		get_engine()
	assert _Session is not None
	return _Session


# --- Models ---

class User(Base):
	__tablename__ = "users"

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
	tg_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
	username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

	expenses: Mapped[Sequence["Expense"]] = relationship(back_populates="user")


class Chat(Base):
	__tablename__ = "chats"

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
	tg_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
	title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

	expenses: Mapped[Sequence["Expense"]] = relationship(back_populates="chat")


class Expense(Base):
	__tablename__ = "expenses"

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
	chat_id: Mapped[str] = mapped_column(String(36), ForeignKey("chats.id", ondelete="CASCADE"))
	user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
	amount: Mapped[float] = mapped_column(Numeric(12, 2))
	category: Mapped[str] = mapped_column(String(64))
	description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

	chat: Mapped[Chat] = relationship(back_populates="expenses")
	user: Mapped[User] = relationship(back_populates="expenses")

	__table_args__ = (
		CheckConstraint("amount > 0", name="expenses_amount_positive_chk"),
	)


# --- Schema helpers ---

async def init_db() -> None:
	engine = get_engine()
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)


# --- CRUD helpers ---

async def ensure_user_and_chat(session: AsyncSession, tg_user_id: int, username: Optional[str], tg_chat_id: int, chat_title: Optional[str]) -> Tuple[User, Chat]:
	user = (await session.execute(select(User).where(User.tg_user_id == tg_user_id))).scalar_one_or_none()
	if user is None:
		user = User(tg_user_id=tg_user_id, username=username)
		session.add(user)

	chat = (await session.execute(select(Chat).where(Chat.tg_chat_id == tg_chat_id))).scalar_one_or_none()
	if chat is None:
		chat = Chat(tg_chat_id=tg_chat_id, title=chat_title)
		session.add(chat)

	await session.flush()
	return user, chat


async def add_expense(session: AsyncSession, chat: Chat, user: User, amount: float, category: str, description: Optional[str]) -> Expense:
	expense = Expense(chat_id=chat.id, user_id=user.id, amount=amount, category=category, description=description)
	session.add(expense)
	await session.flush()
	return expense


async def delete_last_user_expense(session: AsyncSession, chat: Chat, user: User) -> Optional[Expense]:
	q = select(Expense).where(Expense.chat_id == chat.id, Expense.user_id == user.id).order_by(Expense.created_at.desc()).limit(1)
	last = (await session.execute(q)).scalar_one_or_none()
	if last is not None:
		await session.delete(last)
		await session.flush()
	return last


@dataclass
class Totals:
	sum_total: float
	by_user: list[tuple[str, float]]
	by_category: list[tuple[str, float]]


async def totals_for_range(session: AsyncSession, chat: Chat, since: Optional[datetime], until: Optional[datetime]) -> Totals:
	conds = [Expense.chat_id == chat.id]
	if since is not None:
		conds.append(Expense.created_at >= since)
	if until is not None:
		conds.append(Expense.created_at < until)

	total_q = select(func.coalesce(func.sum(Expense.amount), 0)).where(*conds)
	by_user_q = select(User.username, func.coalesce(func.sum(Expense.amount), 0)).join(Expense, Expense.user_id == User.id).where(*conds).group_by(User.username).order_by(func.sum(Expense.amount).desc())
	by_cat_q = select(Expense.category, func.coalesce(func.sum(Expense.amount), 0)).where(*conds).group_by(Expense.category).order_by(func.sum(Expense.amount).desc())

	total = (await session.execute(total_q)).scalar_one()
	by_user = list((await session.execute(by_user_q)).all())
	by_cat = list((await session.execute(by_cat_q)).all())

	return Totals(sum_total=float(total or 0), by_user=[(u or "anon", float(s)) for u, s in by_user], by_category=[(c, float(s)) for c, s in by_cat])


def month_bounds(now_utc: datetime) -> tuple[datetime, datetime]:
	first = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
	if first.month == 12:
		next_first = first.replace(year=first.year + 1, month=1)
	else:
		next_first = first.replace(month=first.month + 1)
	return first, next_first
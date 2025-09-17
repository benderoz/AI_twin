from __future__ import annotations

import google.generativeai as genai

from ..config import settings


genai.configure(api_key=settings.gemini_api_key)


def build_prompt(last_amount: float, category: str, monthly_total: float, humor_level: str = "жестко") -> str:
	return (
		"Сгенерируй одну короткую смешную фразу с очень чёрным юмором и мотивацией экономить. "
		"Мы вносим траты в общем чате. Контекст интересов: спорт (качалка), машины, мотоциклы, одежда, секс, техника, еда/кулинария, тяжёлая музыка, концерты. "
		f"Укажи идею предмета, который можно было бы купить за {monthly_total:.0f} ₽ вместо последних {last_amount:.0f} ₽ на {category}. "
		"Формат: одна фраза, без эмодзи, без дискламеров. Язык — русский."
	)


def generate_dark_humor_line(last_amount: float, category: str, monthly_total: float) -> str:
	model = genai.GenerativeModel("gemini-1.5-flash")
	prompt = build_prompt(last_amount, category, monthly_total)
	resp = model.generate_content(prompt)
	text = (resp.text or "").strip()
	if not text:
		text = "Алкаши ебаные, хватит пить — эти деньги могли стать штангой получше."
	return text
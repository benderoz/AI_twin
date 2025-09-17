from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedExpense:
	amount: float
	category: str
	description: Optional[str]


DEFAULT_CATEGORY = "alcohol"

# User provided categories + synonyms
CATEGORY_SYNONYMS: dict[str, list[str]] = {
	"alcohol": ["алкоголь", "алко", "alcohol", "пиво", "вино", "водка"],
	"smokes": ["курилки", "сиги", "сигареты", "табак", "iqos", "smokes"],
	"fun": ["развлечения", "тусовка", "кино", "концерт", "fun"],
	"restaurants and bars": ["ресторан", "рестораны", "еда", "хавчик", "бар", "bars", "restaurants"],
}

ALL_TOKENS = {token: key for key, tokens in CATEGORY_SYNONYMS.items() for token in tokens}


def parse_expense(text: str) -> Optional[ParsedExpense]:
	if not text:
		return None
	amount_match = re.search(r"(?:(?:^|\s))(\d+[\.,]?\d*)(?:(?:\s|$))", text)
	if not amount_match:
		return None
	amount_str = amount_match.group(1).replace(",", ".")
	try:
		amount = float(amount_str)
	except ValueError:
		return None

	lower = text.lower()
	category = DEFAULT_CATEGORY
	for token, key in ALL_TOKENS.items():
		if re.search(rf"(?<!\S){re.escape(token)}(?!\S)", lower):
			category = key
			break

	description = text.strip()
	# remove amount
	description = description[:amount_match.start()] + description[amount_match.end():]
	# remove category token if present
	if category != DEFAULT_CATEGORY:
		for token in CATEGORY_SYNONYMS[category]:
			pattern = re.compile(rf"(?<!\S){re.escape(token)}(?!\S)", re.IGNORECASE)
			description = pattern.sub(" ", description)

	description = re.sub(r"\s+", " ", description).strip()
	if description == "":
		description = None

	return ParsedExpense(amount=round(amount, 2), category=category, description=description)
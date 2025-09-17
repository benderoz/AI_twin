from __future__ import annotations

import io
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


def circle_crop(image: Image.Image) -> Image.Image:
	mask = Image.new("L", image.size, 0)
	draw = ImageDraw.Draw(mask)
	draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
	result = Image.new("RGBA", image.size)
	result.paste(image, (0, 0), mask=mask)
	return result


def make_collage(avatar1: Image.Image | None, avatar2: Image.Image | None, item_text: str) -> bytes:
	width, height = 800, 450
	canvas = Image.new("RGB", (width, height), (20, 24, 28))
	draw = ImageDraw.Draw(canvas)

	# Place avatars
	def place_avatar(avatar: Optional[Image.Image], box_center_x: int) -> None:
		if avatar is None:
			return
		avatar = avatar.convert("RGB").resize((220, 220))
		avatar = circle_crop(avatar)
		x = box_center_x - avatar.width // 2
		y = height // 2 - avatar.height // 2
		canvas.paste(avatar, (x, y), mask=avatar)

	place_avatar(avatar1, width // 3)
	place_avatar(avatar2, width // 3 * 2)

	# Item text
	try:
		font = ImageFont.truetype("DejaVuSans.ttf", 28)
	except Exception:
		font = ImageFont.load_default()

	draw.text((32, 24), "Могли бы купить:", fill=(240, 240, 240), font=font)
	draw.text((32, 60), item_text, fill=(255, 215, 0), font=font)

	buf = io.BytesIO()
	canvas.save(buf, format="PNG")
	return buf.getvalue()
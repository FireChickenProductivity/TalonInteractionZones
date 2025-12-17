from dataclasses import dataclass
from talon.skia import Rect

@dataclass
class TextArea:
	"""Displays text that cannot be interacted with"""
	text: str
	x: int
	y: int
	width: int
	height: int
	text_color: str
	background_color: str

def draw_text_area(canvas, t: TextArea):
	paint = canvas.paint
	paint.text_align = canvas.paint.TextAlign.LEFT
	paint.textsize = 20
	tr = paint.measure_text(t.text)[1]

	paint.color = t.background_color
	canvas.draw_rect(Rect(t.x, t.y, t.width, t.height))
	paint.color = t.text_color
	canvas.draw_text(t.text, t.x, t.y - tr.y)

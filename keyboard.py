from talon import actions

class Key:
	def __init__(self, main_key: str, secondary_key: str | None = None, is_modifier: bool = False):
		"""Represents a key on the virtual keyboard.

		Args:
			main_key: The primary key
			secondary_key: The key pressed when combined with shift.
			is_modifier: Indicates if the key is a modifier (e.g., Shift, Ctrl).
		"""
		self.main_key = main_key
		self.secondary_key = secondary_key
		self.is_modifier = is_modifier

	def __eq__(self, other) -> bool:
		return (self.main_key == other.main_key and
				self.secondary_key == other.secondary_key and
				self.is_modifier == other.is_modifier)

	def __hash__(self) -> int:
		return hash((self.main_key, self.secondary_key, self.is_modifier))

def create_letter_key(character: str):
	return Key(character.lower(), character.upper())

class Keyboard:
	def __init__(self):
		"""Represents a virtual keyboard where keys can be pressed through eye tracking.
			This provides the information needed to create the interaction zones but does not
			handle eye tracking input itself."""
		self._held_modifiers = set()
		self.rows = [
			[Key("esc"), Key("f1"), Key("f2"), Key("f3"), Key("f4"), Key("f5"), Key("f6"), Key("f7"), Key("f8"), Key("f9"), Key("f10"), Key("f11"), Key("f12")],
			[Key("`", "~"), Key("1", "!"), Key("2", "@"), Key("3", "#"), Key("4", "$"), Key("5", "%"), Key("6", "^"),
			Key("7", "&"), Key("8", "*"), Key("9", "("), Key("0", ")"), Key("-", "_"), Key("+", "="), Key("backspace")
			],
			[Key("tab")] + [create_letter_key(c) for c in "qwertyuiop"] + [Key("[", "{"), Key("]", "}"), Key("\\", "|")],
			[create_letter_key(c) for c in "asdfghjkl"] + [Key(";", ":"), Key("'", '"'), Key("enter")],
			[Key("shift", is_modifier=True)] + [create_letter_key(c) for c in "zxcvbnm"] + [Key(",", "<"), Key(".", ">"), Key("/", "?"), Key("rshift", is_modifier=True)],
			[Key("ctrl", is_modifier=True), Key("alt", is_modifier=True), Key("super", is_modifier=True), Key("space"), Key("rctrl", is_modifier=True), Key("ralt", is_modifier=False), Key("left"), Key("down"), Key("up"), Key("right")]
		]
		self.x: int = 20
		self.y: int = 20
		self._height: int = 0
		self._width: int = 0

	def handle_keypress(self, key: Key):
		"""Handles a key press event, updating the state of held modifiers.
		"""
		if key.is_modifier:
			if key.main_key in self._held_modifiers:
				self._held_modifiers.remove(key.main_key)
			else:
				self._held_modifiers.add(key.main_key)
		else:
			if "shift" in self._held_modifiers:
				keys = [modifier for modifier in self._held_modifiers if modifier != "shift"] + [key.secondary_key]
			else:
				keys = list(self._held_modifiers) + [key.main_key]
			keystroke = "-".join(keys)
			actions.key(keystroke)
			self._held_modifiers.clear()

	def update_size(self, width, height):
		self._width = width
		self._height = height

	def compute_row_key_width(self, row_index: int) -> int:
		row_size = len(self.rows[row_index])
		key_width = int(self._width // row_size)
		return key_width

	def compute_key_height(self) -> int:
		return int(self._height // len(self.rows))
		

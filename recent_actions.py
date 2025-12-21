from talon import Module, actions, app

from collections import deque

class ActionQueue:
	def __init__(self, size: int):
		self.size = size
		self.queue = deque()
	
	def insert(self, entry):
		if entry in self.queue:
			self.queue.remove(entry)
		self.queue.appendleft(entry)
		if len(self.queue) > self.size:
			self.queue.pop()

	def get_items(self):
		return sorted([i for i in self.queue], key=lambda x: x.lower().strip())

	def get_most_recent_items(self, amount: int):
		result = []
		for i in range(amount):
			if i > len(self.queue) - 1:
				break
			result.append(self.queue[i])
		return result

QUEUE_SIZE = 100
insert_queue = ActionQueue(QUEUE_SIZE)
key_queue = ActionQueue(QUEUE_SIZE)

def get_argument(action):
	return action.get_arguments()[0]

def on_action(action):
	if action.get_name() == "insert":
		text = get_argument(action)
		insert_queue.insert(text)
		actions.user.fire_chicken_interaction_zones_handle_insert()
	elif action.get_name() == "key":
		keystroke = get_argument(action)
		key_queue.insert(keystroke)

def on_ready():
	actions.user.basic_action_recorder_register_callback_function_with_name(on_action, "interaction zones listener")

app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:
	def fire_chicken_interaction_zones_get_recent_inserts() -> list[str]:
		"""Returns recently inserted text"""
		return insert_queue.get_items()

	def fire_chicken_interaction_zones_get_recent_keystrokes() -> list[str]:
		"""Returns recent keystrokes"""
		return key_queue.get_items()

	def fire_chicken_interaction_zones_add_recent_insert(text: str):
		"""Adds the specified text to queue of recent inserts"""
		insert_queue.insert(text)

	def fire_chicken_interaction_zones_get_n_recent_inserts(n: int) -> list[str]:
		"""Returns the n most recent inserts"""
		return insert_queue.get_most_recent_items(n)
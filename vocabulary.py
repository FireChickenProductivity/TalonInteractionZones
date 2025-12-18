from .trie import Trie
import os

from talon import app, Module

def load_prefix_information_from_file(path: str) -> Trie:
	trie = Trie("")
	with open(path, "r") as f:
		lines: list[str] = f.readlines()
		for line in lines:
			trie.add_text(line.strip().lower())
	return trie

class Vocabulary:
	__slots__ = ('big_vocabulary')

	def __init__(self):
		current_directory = os.path.dirname(__file__)
		big_vocabulary_path = os.path.join(current_directory, "big_vocabulary.txt")
		self.big_vocabulary = load_prefix_information_from_file(big_vocabulary_path)

	def get_completions_for(self, text: str, limit: int):
		return self.big_vocabulary.get_possibilities(
			text.lower(),
			limit
		)

vocabulary: Vocabulary

def on_ready():
	global vocabulary
	vocabulary = Vocabulary()

app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:
	def interaction_zones_get_completions(text: str, limit: int=20) -> list[str]:
		"""Get interaction zones text completion
			text: the prefix to try to complete
			limit: the maximum number of words to return
		"""
		return vocabulary.get_completions_for(text, limit)
		
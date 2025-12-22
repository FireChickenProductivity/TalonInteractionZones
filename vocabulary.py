from .trie import Trie
import os

from talon import app, Module, settings

def load_prefix_information_from_file(path: str) -> Trie:
	trie = Trie("")
	with open(path, "r") as f:
		lines: list[str] = f.readlines()
		for line in lines:
			trie.add_text(line.strip().lower())
	return trie

def save_word_count_trie(path: str, trie: Trie):
	words_with_metadata = trie.get_possibilities("", 0)
	with open(path, "w") as f:
		for result in words_with_metadata:
			word, count = result
			f.write(f"{word},{count}\n")

def save_new_word(path: str, word: str):
	with open(path, "a") as f:
		f.write(f"{word},1\n")

def add_numbers(a, b):
	return a+b

def load_word_count_trie(path: str):
	trie = Trie("")
	with open(path, "r") as f:
		lines: list[str] = f.readlines()
		for line in lines:
			word, count = line.split(",")
			count = int(count)
			trie.add_text(word, count, add_numbers)
	return trie

class Vocabulary:
	"""Offers word completion options"""
	__slots__ = ('big_vocabulary', 'personal_vocabulary', 'personal_vocabulary_path', 'personal_vocabulary_changed')

	def __init__(self):
		current_directory = os.path.dirname(__file__)
		big_vocabulary_path = os.path.join(current_directory, "big_vocabulary.txt")
		self.big_vocabulary = load_prefix_information_from_file(big_vocabulary_path)
		self.personal_vocabulary_path = os.path.join(current_directory, "personal_vocabulary.txt")
		if os.path.exists(self.personal_vocabulary_path):
			self.personal_vocabulary = load_word_count_trie(self.personal_vocabulary_path)
		else:
			self.personal_vocabulary = Trie("")
		self.personal_vocabulary_changed = False

	def get_completions_for(self, text: str, limit: int):
		"""Offer at most limit word completion options for the text given"""
		personalized_options = self.personal_vocabulary.get_possibilities(
			text.lower(),
			settings.get("user.fire_chicken_interaction_zones_number_of_personal_words_to_consider")
		)
		
		# pick best limit personalized options
		if len(personalized_options) <= limit:
			options = personalized_options
		else:
			options = sorted(personalized_options, key=lambda x: x[1])[:limit]
		options = sorted([option[0] for option in options])
		if len(options) < limit:
			big_options = self.big_vocabulary.get_possibilities(
				text.lower(),
				limit - len(options)
			)
			options.extend(big_options)
		return options

	def handle_word_used_by_user(self, word: str):
		"""Update personal vocabulary in response to a word used by the user"""
		self.personal_vocabulary_changed = True
		lower = word.lower()
		was_present = self.personal_vocabulary.contains(lower)
		self.personal_vocabulary.add_text(lower, 1, add_numbers)
		if not was_present:
			save_new_word(self.personal_vocabulary_path, lower)

	def save_personal_vocabulary(self):
		"""Save the personal vocabulary. This may be an expensive operation, so do not run after each word is used"""
		if self.personal_vocabulary_changed:
			save_word_count_trie(self.personal_vocabulary_path, self.personal_vocabulary)
			self.personal_vocabulary_changed = False

vocabulary: Vocabulary

def on_ready():
	global vocabulary
	vocabulary = Vocabulary()

app.register("ready", on_ready)

mod = Module()

mod.setting(
	"fire_chicken_interaction_zones_number_of_personal_words_to_consider",
	type=int,
	default=1000,
	desc="The maximum number of words from the personal vocabulary to consider during fire chicken interaction zones word completions"
)

@mod.action_class
class Actions:
	def interaction_zones_get_completions(text: str, limit: int=20) -> list[str]:
		"""Get interaction zones text completion
			text: the prefix to try to complete
			limit: the maximum number of words to return
		"""
		return vocabulary.get_completions_for(text, limit)
	
	def interaction_zones_handle_word_used_by_user(word: str):
		"""Update vocabulary data in response to the user typing a word"""
		vocabulary.handle_word_used_by_user(word)

	def interaction_zones_save_vocabulary():
		"""Saves the vocabulary to disk. This may be an expensive operation."""
		vocabulary.save_personal_vocabulary()

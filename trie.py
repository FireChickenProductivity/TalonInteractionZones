class Trie:
	__slots__ = ('char', 'children')

	def __init__(self, char: str):
		self.char = char
		self.children = {}

	def add_child(self, char):
		if char not in self.children:
			self.children[char] = Trie(char)
		return self.children[char]

	def add_text(self, text):
		trie = self
		for c in text:
			trie = trie.add_child(c)
		trie.add_child("")

	def get_possibilities(self, prefix: str, limit: int):
		"""
			Find limit items with the specified prefix
			Ignore character at the current level. This is empty for the head.
			Uses breath first search.
		"""
		try:
			matching_child = prefix
		except ValueError:
			return []
			
		results = []
		current_level = [(matching_child, prefix)]
		next_level = []
		while current_level:
			for child, current_prefix in current_level:
				for nested_child in child.children:
					nested_character = nested_child.char
					total = current_prefix + nested_character
					if nested_character == "":
						results.append(total)
						if len(total) >= limit:
							return results
					else:
						next_level.append((nested_child, total))
			current_level = next_level[:]
			next_level = []
		return results

	def compute_child_matching_prefix(self, prefix: str):
		trie = self
		for c in prefix:
			if c not in trie.children:
				raise ValueError()
			trie = trie.children[c]
		return trie
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
			matching_child = self.compute_child_matching_prefix(prefix)
		except ValueError:
			return []
			
		results = []
		current_level = [(matching_child, prefix)]
		next_level = []
		while current_level:
			for child, current_prefix in current_level:
				for nested_child in child.children.values():
					nested_character = nested_child.char
					total = current_prefix + nested_character
					if nested_character == "":
						results.append(total)
						if len(results) >= limit:
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

# for testing
if __name__ == '__main__':
	def create_from_iterable(source):
		"""Create a trie on all the text in the source"""
		prefixes = Trie("")
		for text in source:
			prefixes.add_text(text)
		return prefixes
	def recreates_source(source, prefix: str="") -> bool:
		"""Returns true if a trie can successfully recreate all the text in the source with the specified prefix"""
		prefixes = create_from_iterable(source)
		possibilities = prefixes.get_possibilities(prefix, len(source))
		expected = set([t for t in source if t.startswith(prefix)])
		return set(possibilities) == expected

	def test_recreates_source(source, prefix: str=""):
		"""creates a trie on all the text in the source
			and prints information on if all the information from that source can be recreated
		"""
		was_successful = recreates_source(source, prefix)
		print(source, prefix, was_successful)
		if not was_successful:
			prefixes = create_from_iterable(source)
			possibilities = prefixes.get_possibilities(prefix, len(source))
			print('    possibilities', possibilities)

	longer_list = ["ab", "ba", "bad", "barn", "bread", "cow"]
	test_cases = (
		(["a"], ""),
		(["ab", "b"], ""),
		(["ab", "ba"], ""),
		(longer_list, ""),
		(longer_list, "a"),
		(longer_list, "b"),
		(longer_list, "c"),
		(longer_list, "d"),
		(longer_list, "ba"),
		(longer_list, "bar"),
		(longer_list, "barn"),
		(longer_list, "bread"),
		(longer_list, "breading"),
	)
	for test_case in test_cases:
		test_recreates_source(*test_case)
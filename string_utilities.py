def compute_last_word(text: str):
	"""Computes the last word of the text.
		A lowercase letter followed by an upper case letter indicates that the upper case later is the start of the word.
	"""
	i = len(text)
	was_upper = False
	while i > 0 and text[i-1].isalpha() and (not (text[i-1].islower() and was_upper)):
		was_upper = text[i-1].isupper()
		i -= 1
	if i == len(text):
		return ""
	return text[i:]

def compute_words(text: str):
	result = []
	start = 0
	end = 0
	was_lower = False
	while end < len(text):
		is_not_alpha = not (text[end].isalpha())
		if is_not_alpha or (text[end].isupper() and was_lower):
			if end > start:
				result.append(text[start:end])
			if is_not_alpha:
				start = end+1
			else:
				start = end
		was_lower = text[end].islower()
		end += 1
	if end > start:
		result.append(text[start:end])
	return result

if __name__ == '__main__':
	def test_compute_words(text, expected):
		result = compute_words(text)
		if result != expected:
			print(f"expected {expected} but got {result}")
	test_cases = (
		("word", ["word"]),
		("apple sandwich", ["apple", "sandwich"]),
		("apple sandwich ", ["apple", "sandwich"]),
		("this_is_a_variable", ["this", "is", "a", "variable"]),
		("variableName", ["variable", "Name"]),
	)
	for test_case in test_cases:
		test_compute_words(*test_case)

	def test_compute_last_word(text, expected):
		result = compute_last_word(text)
		if expected != result:
			print(f"expected {expected} but got {result}")

	last_word_test_cases = (
		("word", "word"),
		("_", ""),
		("variableName", "Name"),
		("variable_names", "names"),
	)
	for test_case in last_word_test_cases:
		test_compute_last_word(*test_case)
		
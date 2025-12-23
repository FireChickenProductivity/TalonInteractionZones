def compute_last_word(text: str):
	i = len(text)
	while i > 0 and text[i-1].isalpha():
		i -= 1
	if i == len(text):
		return ""
	return text[i:]

def compute_words(text: str):
	result = []
	start = 0
	end = 0
	while end < len(text):
		if not text[end].isalpha():
			if end > start:
				result.append(text[start:end])
			start = end+1
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
	)
	for test_case in test_cases:
		test_compute_words(*test_case)
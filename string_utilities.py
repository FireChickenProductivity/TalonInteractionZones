def compute_last_word(text: str):
	i = len(text)
	while i > 0 and text[i-1].isalpha():
		i -= 1
	if i == len(text):
		return ""
	return text[i:]
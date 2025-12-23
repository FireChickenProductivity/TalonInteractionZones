# a slice menu lets the user pick from a slice of available text
# as an argument to an operation
# each slice position is specified by the line number and index on that line

from talon import actions

class SliceMenu:
	__slots__ = ('options', 'action', '_start', 'selection_finished_callback')
	def __init__(self, options, action, selection_finished_callback):
		self.options = options
		self.action = action
		self._start = None
		self.selection_finished_callback = selection_finished_callback

	def handle_input(self, line_number, index):
		"""
		line_number: the index of the option
		index: the index within the option
		this corresponds to picking part of the slice (start or ending)
		"""
		if self._start is None:
			self._start = (line_number, index)
		else:
			end = (line_number, index)
			start, end = sort_slice_positions(self._start, end)
			self.action(self.options, start, end)
			self._start = None
			self.selection_finished_callback()

def insert_slice(options, start, end):
	text = compute_text(options, start, end)
	actions.user.fire_chicken_interaction_zones_paste(text)

def compute_text(options, start, end) -> str:
	first_line = start[0]
	second_line = end[0]
	first_index = start[1]
	second_index = end[1]
	if first_line == second_line:
		return "".join(options[first_line][first_index:second_index+1])
	relevant_lines = []
	relevant_lines.append(
		"".join(options[first_line][first_index:])
 	)
	if second_line - first_line > 1:
		relevant_lists = options[first_line+1:second_line]
		relevant_lines.extend(["".join(line) for line in relevant_lists])
	relevant_lines.append(
		"".join(options[second_line][:second_index+1])
	)
	return "\n".join(relevant_lines)

def sort_slice_positions(start, end):
	if (start[0] > end[0]) or ((start[0] == end[0]) and (start[1] > end[1])):
		return end, start
	return start, end

def compute_slice_menu_tokens(line:str):
	result = []
	current_start = 0
	current_end = 0
	previous_category = None
	for c in line:
		category = compute_token_category(c)
		if (previous_category is not None) and (previous_category != category):
			result.append(line[current_start:current_end])
			current_start = current_end
		previous_category = category
		current_end += 1
	result.append(line[current_start:])
	return result

def compute_token_category(token: str):
	if token.isspace():
		return 0
	elif token.isalpha():
		return 1 if token.islower() else 2
	elif token.isdigit():
		return 3
	else:
		return 4


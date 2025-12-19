from talon import Module, actions

mod = Module()
@mod.action_class
class Actions:
	def fire_chicken_interaction_zones_get_selected_text() -> str:
		"""Returns the selected text"""
		return actions.edit.selected_text()

	def fire_chicken_interaction_zones_select_up(n: int):
		"""Selects the specified number of lines up"""
		actions.edit.extend_line_start()
		for _ in range(n):
			actions.edit.extend_up()
		actions.edit.extend_line_start()

	def fire_chicken_interaction_zones_select_down(n: int):
		"""Selects the specified number of lines down"""
		actions.edit.extend_line_end()
		for _ in range(n):
			actions.edit.extend_down()
		actions.edit.extend_line_end()
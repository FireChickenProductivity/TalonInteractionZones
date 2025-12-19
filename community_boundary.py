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

	def fire_chicken_interaction_zones_copy_up(n: int) -> str:
		"""Copy the following lines above the cursor"""
		actions.user.fire_chicken_interaction_zones_select_up(n)
		result = actions.user.fire_chicken_interaction_zones_get_selected_text()
		actions.edit.right()
		return result

	def fire_chicken_interaction_zones_copy_down(n: int) -> str:
		"""Copy the following lines below the cursor"""
		actions.user.fire_chicken_interaction_zones_select_down(n)
		result = actions.user.fire_chicken_interaction_zones_get_selected_text()
		actions.edit.left()
		return result

	def fire_chicken_interaction_zones_paste(text: str):
		"""Pastes the specified text"""
		actions.user.paste(text)
		
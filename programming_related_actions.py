from talon import Module, actions

mod = Module()

@mod.action_class
class Actions:
	def fire_chicken_interaction_zones_slap_back():
		"""Insert line down and then press backspace"""
		actions.edit.line_insert_down()
		actions.edit.delete()
	
	def fire_chicken_interaction_zones_slap_twice_back():
		"""Insert line down twice and then press backspace"""
		actions.edit.line_insert_down()
		actions.edit.line_insert_down()
		actions.edit.delete()
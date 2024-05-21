import os
from talon import Module, app
from .master import toggle_showing

def set_up():
    from .master import setup
    setup()

app.register('ready', set_up)

module = Module()
@module.action_class
class Actions:
    def interaction_zones_toggle_showing():
        """Toggle the visibility of the interaction zones"""
        try:
            toggle_showing()
        except Exception as e:
            print(str(e))

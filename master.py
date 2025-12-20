from talon import ui, canvas, cron, ctrl, actions
from talon.skia import Rect
import os
import math
from typing import Union, Callable
from .helpers import rgba2hex, verify_home_dir, TRANSPARENT, TriggerType
from .config_parser import parse_zone,is_line_newzone,is_line_endzone
from .settings import *
from .zones import SimpleZone, create_simple_zone
from .keyboard import Keyboard, Key
from .text_area import TextArea, draw_text_area
from .zone_management import ZoneManager
from .slice_menu import SliceMenu, insert_slice, compute_slice_menu_tokens

HOME_DIRECTORY = verify_home_dir()
ZONE_SIZE = 200

SNIPPET_ACTION_PREFIX = "snippet: "
OPERATOR_ACTION_PREFIX = "operator: "
SPECIAL_SWAP_NAME_PREFIX = ":"
SNIPPET_ZONE_NAME = "SNIPPET"
OPERATOR_ZONE_NAME = "OPERATOR"
RECENT_INSERTS_ZONE_NAME = "RECENT_INSERT"
RECENT_KEYSTROKES_ZONE_NAME = "RECENT_KEYSTROKE"
KEYBOARD_ZONE_NAME = "KEYBOARD"
EDIT_ACTIONS_ZONE_NAME = "EDIT"
SLICE_MENU_ZONE_NAME = "SLICE_MENU"
SPECIAL_ZONE_NAMES = set([SNIPPET_ZONE_NAME, OPERATOR_ZONE_NAME, RECENT_INSERTS_ZONE_NAME, RECENT_KEYSTROKES_ZONE_NAME, KEYBOARD_ZONE_NAME, EDIT_ACTIONS_ZONE_NAME, SLICE_MENU_ZONE_NAME])

class Master:
    __slots__ = (
        'displays', 'showZones', 'screen', 'screenRect', 'zonesRect', 'canvas', 'configs',
        'activeID', 'toggleRect', 'lastWindowTitle', 'activeZoneSet', 'overrideZoneSet', 'updateTriggered',
        'keyboard', 'job', 'job2', 'zone_manager', 'previous_zone',
        'slice_menu')
    def __init__(self) -> None:
        self.displays = {}
        self.showZones = False
        self.zone_manager = ZoneManager()
        
        # I am not sure about multiple screens here, but it could be theoretically supported
        screens = ui.screens()
        self.screen = screens[0]
        self.screenRect = self.screen.rect.copy()
        self.zonesRect = self.screenRect
        self.canvas = canvas.Canvas.from_screen(self.screen)
        
        self.configs = dict()
        self.activeID=TRANSPARENT
        
        w=60 if not ZONE_TOGGLE_OVERRIDE_SIZE else ZONE_TOGGLE_OVERRIDE_WIDTH
        h=30 if not ZONE_TOGGLE_OVERRIDE_SIZE else ZONE_TOGGLE_OVERRIDE_HEIGHT
        if ZONE_TOGGLE_OVERRIDE_POSITION:
            self.toggleRect=(Rect(ZONE_TOGGLE_OVERRIDE_X,ZONE_TOGGLE_OVERRIDE_Y,w,h))
        else:
            self.toggleRect=(Rect(self.screen.width/2 - w/2,10,w,h))
        
        self.lastWindowTitle = ""
        self.activeZoneSet = ""
        self.previous_zone = ""
        self.overrideZoneSet=None
        self.updateTriggered=False
        self.keyboard: Keyboard = Keyboard(self.update_keyboard_current_text)
        self.keyboard.update_size(self.screen.width, self.screen.height//2)
        self.slice_menu = None

    def set_zone_override(self,zoneSet):
        self.previous_zone = self.overrideZoneSet
        self.overrideZoneSet=zoneSet
        self.updateTriggered = True

    def return_to_previous_zone(self):
        if self.previous_zone:
            self.set_zone_override(self.previous_zone)
        else:
            self.set_zone_override(DEFAULT_FILE_NAME)

    def enable(self,showZones) -> None:  
        self.canvas.register("draw", self.draw)        
        self.job = cron.interval('16ms', self.update)        
        self.job2 = cron.interval('100ms', self.slow_update)        
        self.canvas.register("mouse", self.on_mouse)
        if showZones:
            self.show()      
            
    def show(self):
        self.showZones = False
        self.activeZoneSet=""
        self.zone_manager.clear()
        if is_special_zone(self.overrideZoneSet):
            self.show_special_zone_set()
        else:
            self.show_file()

    def show_special_zone_set(self):
        name = compute_special_zone_name(self.overrideZoneSet)
        if name in SPECIAL_ZONE_NAMES:
            self.activeZoneSet = name
        if name == SNIPPET_ZONE_NAME:
            relevant_snippet_names = compute_active_snippet_names()
            insert_actions = ["snippet: " + name for name in relevant_snippet_names]
            self.show_zone_for_list(relevant_snippet_names, insert_actions)
        elif name == RECENT_INSERTS_ZONE_NAME:
            recent_inserts = actions.user.fire_chicken_interaction_zones_get_recent_inserts()
            def insert_text(text):
                self.return_to_previous_zone()
                actions.insert(text)
            def create_insert_operator(text):
                return lambda: insert_text(text)
            insert_actions = [create_insert_operator(text) for text in recent_inserts]
            self.show_zone_for_list(recent_inserts, insert_actions)
        elif name == RECENT_KEYSTROKES_ZONE_NAME:
            recent_keystrokes = actions.user.fire_chicken_interaction_zones_get_recent_keystrokes()
            def press_keystroke(keystroke):
                self.return_to_previous_zone()
                actions.key(keystroke)
            def create_operator(keystroke):
                return lambda: press_keystroke(keystroke)
            key_stroke_actions = [create_operator(keystroke) for keystroke in recent_keystrokes]
            self.show_zone_for_list(recent_keystrokes, key_stroke_actions)
        elif name == OPERATOR_ZONE_NAME:
            operator_names = actions.user.interaction_zones_get_community_operator_names()
            def insert_operator(operator_name):
                try:
                    actions.user.code_operator(operator_name)
                except Exception as ex:
                    print('operator_name', operator_name)
                self.return_to_previous_zone()
            def create_lambda(operator_name):
                return lambda: insert_operator(operator_name)
            corresponding_actions = [create_lambda(operator_name) for operator_name in operator_names]
            self.show_zone_for_list(operator_names, corresponding_actions)
        elif name == EDIT_ACTIONS_ZONE_NAME:
            edit_actions = actions.user.interaction_zones_get_edit_actions()
            names = [a[0] for a in edit_actions]
            corresponding_actions = [a[1] for a in edit_actions]
            self.show_zone_for_list(names, corresponding_actions)
        elif name == KEYBOARD_ZONE_NAME:
            self.show_keyboard()
        elif name == SLICE_MENU_ZONE_NAME:
            self.show_slice_menu()

    def show_keyboard(self):
        def create_key_operator(key: Key):
            return lambda: self.keyboard.handle_keypress(key)
                
        x = self.keyboard.x
        y = self.keyboard.y
        key_height = self.keyboard.compute_key_height()
        scaling_factor = 0.50
        adjusted_height = round(key_height * scaling_factor)
        for row_index in range(len(self.keyboard.rows)):
            key_width = self.keyboard.compute_row_key_width(row_index)
            adjusted_width = round(key_width * scaling_factor)
            for key in self.keyboard.rows[row_index]:
                key_text = f"{key.main_key} / {key.secondary_key}" if key.secondary_key else key.main_key
                center_x = x + key_width // 2
                center_y = y + key_height // 2
                zone = SimpleZone(color="#7aacddff", name=key_text, ttype=TriggerType.HOVER, action=create_key_operator(key), warmup=1, repeatTime=1, modifiers="", centre=(center_x, center_y), dimensions=(adjusted_height, adjusted_width))
                
                self.zone_manager.add_zone(zone)
                x += key_width
            y += key_height
            x = self.keyboard.x
        swap_zones = (
            ("default", "default"),
            ("operator", ":OPERATOR"),
            ("edit", ":EDIT"),
        )
        slice_menu_zones = (
            (True, insert_slice, "bring up"),
            (False, insert_slice, "bring down"),
        )
        common_programing_actions = (
            ("assign", lambda: actions.user.code_operator("ASSIGNMENT")),
            ("slap", lambda: actions.edit.line_insert_down()),
            ("comma space", lambda: actions.insert(", ")),
            ("tail", lambda: actions.edit.line_end()),
        )
        special_row_length = len(swap_zones) + len(slice_menu_zones) + len(common_programing_actions)
        special_row_width = round(self.keyboard.get_width()/special_row_length)
        special_row_dimensions = (key_height, round(special_row_width*scaling_factor))
        center_x = x + special_row_width // 2
        center_y = y + key_height // 2
        for name, target in swap_zones:
            zone = create_simple_zone(
                "swap " + name,
                "swap: " + target,
                (center_x, center_y),
                special_row_dimensions
            )
            self.zone_manager.add_zone(zone)
            center_x += special_row_width
        for is_up, target, name in slice_menu_zones:
            if is_up:
                action = lambda: self.show_select_up_slice_menu(target)
            else:
                action = lambda: self.show_select_down_slice_menu(target)
            zone = create_simple_zone(
                name,
                action,
                (center_x, center_y),
                special_row_dimensions
            )
            self.zone_manager.add_zone(zone)
            center_x += special_row_width
        for name, action in common_programing_actions:
            zone = create_simple_zone(
                name,
                action,
                (center_x, center_y),
                special_row_dimensions
            )
            self.zone_manager.add_zone(zone)
            center_x += special_row_width
        self.showZones = True
        self.zone_manager.add_text_area(TextArea(
            "",
            self.keyboard.x,
            self.keyboard.y,
            200,
            30,
            rgba2hex(255,255,255,ZONES_TEXT_ALPHA),
            "#7aacddff",
        ))

    def update_keyboard_current_text(self, text: str, previous: str):
        """text: the current keyboard text
            previous: the previous keyboard text
        """
        if (text == "") and (previous != "") and (len(previous) > 2):
            actions.user.fire_chicken_interaction_zones_add_recent_insert(previous)
        self.zone_manager.update_text_area_text(0, text)
        self.zone_manager.remove_temporary_zones()
        row_number: int = 0
        if text:
            snippet_names = compute_active_snippet_names()
            matching_snippet_names = [
                name for name in snippet_names
                if name.startswith(text)
            ]
            
            if matching_snippet_names:
                row_number += 1
                def snippet_action(name: str):
                    for _ in range(len(text)):
                        actions.edit.delete()
                    actions.user.insert_snippet_by_name(name)
                def create_snippet_lambda(name):
                    return lambda: snippet_action(name)
                corresponding_actions = [create_snippet_lambda(name) for name in matching_snippet_names]
                self.add_temporary_keyboard_row(matching_snippet_names, corresponding_actions, row_number)
            word_completions = actions.user.interaction_zones_get_completions(text.lower(), 20)
            def completion_action(completion):
                original = text
                extra = completion[len(original):]
                actions.insert(extra)
                self.keyboard.set_current_text(original + extra)
            def create_completion_lambda(completion):
                return lambda: completion_action(completion)
            if word_completions:
                row_number += 1
                corresponding_actions = [create_completion_lambda(c) for c in word_completions]
                self.add_temporary_keyboard_row(word_completions, corresponding_actions, row_number)
            recent_inserts = actions.user.fire_chicken_interaction_zones_get_recent_inserts()
            matching_inserts = [t for t in recent_inserts
                            if t.startswith(text) and len(text) < len(t)]
            if matching_inserts:
                row_number += 1
                corresponding_actions = [create_completion_lambda(c) for c in matching_inserts]
                self.add_temporary_keyboard_row(matching_inserts, corresponding_actions, row_number)
                    
                
    def add_temporary_keyboard_row(self, names, corresponding_actions, row_number: int):
        """
            Add a row at the bottom of the keyboard with
            names as the display text and corresponding_actions
            as the actions to perform on interaction
            row_number: the number for the additional row
            starts from 1
        """
        x = self.keyboard.x
        height = self.keyboard.compute_key_height()
        y = (len(self.keyboard.rows)+row_number)*height + self.keyboard.y
        width = round(self.keyboard.get_width()//len(names))
        for i in range(len(names)):
            name = names[i]
            zone = SimpleZone(
                "",
                (x + width//2, y + height//2),
                name,
                TriggerType.HOVER,
                corresponding_actions[i],
                1,
                1,
                "",
                (height//2, width//2)
            )
            self.zone_manager.add_temporary_zone(
                zone
            )
            x += width
        
    def show_zone_for_list(self, names, corresponding_actions):
        if len(names) != len(corresponding_actions):
            print("The number of names in the list did not match the number of actions!")
            return 
        zone_number = 0
        left = self.zonesRect.left
        top = self.zonesRect.top
        height = self.zonesRect.height
        width = self.zonesRect.width
        number_of_actions = len(names) + 2 # add 2 for navigation actions
        number_per_row_and_column = math.ceil(math.sqrt(number_of_actions))
        zone_width = math.floor(width/number_per_row_and_column)
        zone_height = math.floor(height/number_per_row_and_column)
        zone_dimensions = (math.floor(0.65*zone_height), math.floor(0.65*zone_width))
        def compute_dimensions(id):
            x = left + ((id % number_per_row_and_column) + 1)*zone_width - 0.5*zone_width
            y = top + ((id//number_per_row_and_column) + 1)*zone_height - 0.5*zone_height
            return x, y
        
        for n, action in zip(names, corresponding_actions):
            x, y = compute_dimensions(zone_number)
            zone = SimpleZone(color="#7aacddff", name=n, ttype=TriggerType.HOVER, action=action, warmup=1, repeatTime=1, modifiers="", centre=(x, y), dimensions=zone_dimensions)
            self.zone_manager.add_zone(zone)
            zone_number += 1
        x, y = compute_dimensions(zone_number)
        return_to_default_zone = create_simple_zone(
            "swap default",
            "swap: default",
            (x, y),
            zone_dimensions
        )
        self.zone_manager.add_zone(return_to_default_zone)
        zone_number += 1
        x, y = compute_dimensions(zone_number)
        keyboard_zone = create_simple_zone(
            "swap keyboard",
            "swap: :KEYBOARD",
            (x, y),
            zone_dimensions
        )
        self.zone_manager.add_zone(keyboard_zone)
        self.showZones = True

    def show_select_up_slice_menu(self, action):
        option_text = actions.user.fire_chicken_interaction_zones_copy_up(SLICE_MENU_SELECTION_AMOUNT)
        options = option_text.split("\n")
        self.update_slice_menu(options, action)

    def show_select_down_slice_menu(self, action):
        option_text = actions.user.fire_chicken_interaction_zones_copy_down(SLICE_MENU_SELECTION_AMOUNT)
        options = option_text.split("\n")
        self.update_slice_menu(options, action)

    def update_slice_menu(self, options: list[str], action):
        tokens = [compute_slice_menu_tokens(option) for 
                  option in options]
        self.slice_menu = SliceMenu(tokens, action, self.return_to_previous_zone)
        self.set_zone_override(SPECIAL_SWAP_NAME_PREFIX + SLICE_MENU_ZONE_NAME)

    def show_slice_menu(self):
        self.showZones = True
        options = self.slice_menu.options
        left = self.zonesRect.left
        top = self.zonesRect.top
        height = self.zonesRect.height
        width = self.zonesRect.width
        y = top
        delta_y = math.floor(height/len(options))
        zone_height = round(delta_y*.8)
        def create_lambda(line_number, i):
            return lambda : self.slice_menu.handle_input(line_number, i)
        for line_number, line in enumerate(options):
            # display line
            if (len(line) == 0) or ((len(line) == 1) and (line[0].isspace())):
                continue
            x = left
            delta_x = math.floor(width/(len(line)))
            zone_width = round(delta_x*.8)
            for i, c in enumerate(line):
                if c.isspace():
                    c = ""
                zone = create_simple_zone(
                    c,
                    create_lambda(line_number, i),
                    (x + round(zone_width/2), y + round(zone_height/2)),
                    (zone_height, zone_width)
                )
                self.zone_manager.add_zone(zone)
                x += delta_x
            y += delta_y

    def show_file(self):
        optimal_name = self.get_optimal_file_name()
        s=os.path.join(HOME_DIRECTORY, optimal_name)
        try:
            with open("%s.txt" % (s),"r") as f:
                lines = f.readlines()
                lines.append(" ")
                ss = ""
                for s in lines:
                    if is_line_newzone(s):
                        ss = s
                    elif not is_line_endzone(s):
                        ss+=s
                    else:
                        z=parse_zone(ss)
                        if z != None:
                            self.zone_manager.add_zone(z)
                        else:
                            print("Failed to parse zone with config\n%s"%ss)
            
            self.activeZoneSet = optimal_name
            
            print("Passed config parsing stage with %s"%self.activeZoneSet)
            self.showZones = True
        except FileNotFoundError:
            print("Either configuration file txt or image png not found (%s)."%s)
            return

    def disable(self) -> None:        
        self.canvas.unregister("draw", self.draw) 
        self.canvas.unregister("mouse", self.on_mouse)
        cron.cancel(self.job)
        cron.cancel(self.job2)
    def hide(self):
        self.deactivate_zones()
        self.showZones = False        
       
    def deactivate_zones(self):
        if not self.showZones:
            return
        self.zone_manager.deactivate_zones()
        
    def draw(self, canvas) -> None:  
        paint = canvas.paint
                
        if self.showZones:
            paint.color = rgba2hex(64,128,64,ZONE_TOGGLE_SWITCH_ALPHA)
        else:
            paint.color = rgba2hex(128,128,128,ZONE_TOGGLE_SWITCH_ALPHA)
        if TOGGLE_ZONE_ENABLED: canvas.draw_rect(self.toggleRect)
        
        if SHOW_WINDOW_NAME:
            paint.color = rgba2hex(255,255,255,200)
            text = self.get_active_window_title()
            tr = paint.measure_text(text)[1]
            center = self.toggleRect.center
            canvas.draw_text(text,center.x-tr.width/2,center.y+tr.height*3)  
              
        if self.showZones==False:
            return

        paint.color = rgba2hex(255,255,255,ZONES_ALPHA)
        
        zones = self.zone_manager.copy_zones()
        for z in zones.values():
            z.draw(canvas)
        
        for t in self.zone_manager.copy_text_areas():
            draw_text_area(canvas, t)
    
    def on_mouse(self, event):
        x, y = ctrl.mouse_pos()  
            
        if TOGGLE_ZONE_ENABLED and event.event=="mouseup" and self.toggleRect.contains(x,y):
            self.toggle_showing()
        
        if not self.showZones:
            return
        
        id = self.activeID
        if event.event=="mouseup" and id != TRANSPARENT:
            self.zone_manager.click(id)
            pass

    def toggle_showing(self):
        if not self.showZones:
            self.show()
        else:
            self.hide()
    
    def update(self):   
        if self.showZones:        
            colorID = self.get_active_zone_id()
            self.activeID=colorID
            self.zone_manager.update(self.activeID)

    def should_update(self):
        return self.updateTriggered or (not is_special_zone(self.overrideZoneSet) and (self.activeZoneSet != self.get_optimal_file_name()))

    def slow_update(self):
        if not self.showZones:
            return
        t = self.get_active_window_title()
        if self.should_update():
            self.hide()
            self.show()
            self.updateTriggered = False

        if t != self.lastWindowTitle:
           self.set_zone_override(None)
        self.lastWindowTitle = t
        pass
    
    def get_active_zone_id(self):
        x, y = ctrl.mouse_pos() 
        if not self.zonesRect.contains(x,y):
            return TRANSPARENT
        color = self.zone_manager.get_color(x, y)
        return color
      
    def get_optimal_file_name(self):
        validFiles = list()
        for file in os.listdir(HOME_DIRECTORY):
            if file.endswith(".txt"):
                validFiles.append(file[:len(file)-4])
        
        if self.overrideZoneSet != None:
            if self.overrideZoneSet not in validFiles:
                print("Failed to find '%s', keeping default."%self.overrideZoneSet)
                self.overrideZoneSet=None
                return self.get_optimal_file_name()
            return self.overrideZoneSet
                
        if not EXPERIMENTAL_AUTO_ZONE_CHANGE:
            return DEFAULT_FILE_NAME
                
        if len(validFiles) == 1:
            return validFiles[0]
                
        t = self.get_active_window_title()
        for f in validFiles:
            if f in t:
                return f
        
        return DEFAULT_FILE_NAME
    
    def get_active_window_title(self):
        return ui.active_window().title
     
master = None

def setup():
    global master
    master = Master()
    master.enable(DEFAULT_SHOW)
    
def primative_interaction(action:Union[Callable, str]):
    """All interactions ever fired are fired here."""
    global master
    if master is None:
        return 
    if isinstance(action, Callable):
        action()
        return 
    
    try:
        if action[:5]=="bind:":
            actions.user.keybinder_add_key_bind(action[6:].replace('\n',''))
            pass
        elif action[:7]=="unbind:":
            actions.user.keybinder_remove_key_bind(action[8:].replace('\n',''))
        elif action[:5]=="swap:":
            master.set_zone_override(action[6:].strip())
        elif action == 'language': 
            zone_override = actions.code.language()
            master.set_zone_override(zone_override.replace('\n',''))
        elif action[:12]=="scroll down:":
           actions.user.mouse_scroll_down(float(action[13:].replace('\n','')))     
        elif action[:10]=="scroll up:":
           actions.user.mouse_scroll_up(float(action[11:].replace('\n','')))
        elif action[:6]=="mimic:": # Not recommended for usage generally (can cause unexpected behaviour)
            actions.user.engine_mimic(action[7:].replace('\n',''))
        elif action.startswith(SNIPPET_ACTION_PREFIX):
            snippet_name = action[len(SNIPPET_ACTION_PREFIX):]
            if len(snippet_name) == 0:
                print("Snippet interaction zone action is missing name!")
            else:
                actions.user.insert_snippet_by_name(snippet_name)
                master.return_to_previous_zone()
        elif action.startswith(OPERATOR_ACTION_PREFIX):
            operator_name = action[len(OPERATOR_ACTION_PREFIX):]
            actions.user.code_operator(operator_name)
            master.return_to_previous_zone()
        elif not (action.startswith(' ') or action.endswith(' ')):
            actions.key(action)
        else:
            raise ValueError("Action not recognized")
    except ValueError:
        actions.insert(action)
    except Exception as e:
        print(str(e))

def toggle_showing():
    global master
    if master is not None:
        master.toggle_showing()

def is_special_zone(override_name) -> bool:
    if override_name is None:
        return False
    if not override_name.startswith(SPECIAL_SWAP_NAME_PREFIX):
        return False
    name = compute_special_zone_name(override_name)
    return name in SPECIAL_ZONE_NAMES

def compute_special_zone_name(override_name: str) -> str:
    return override_name[len(SPECIAL_SWAP_NAME_PREFIX):]

def compute_active_snippet_names() -> list[str]:
    snippet_names = actions.user.get_snippet_names()
    relevant_snippet_names = []
    for snippet_name in snippet_names:
        try:
            snippet = actions.user.get_snippet(snippet_name)
            if snippet:
                relevant_snippet_names.append(snippet_name)
        except Exception:
            pass
    relevant_snippet_names = sorted(relevant_snippet_names)
    return relevant_snippet_names
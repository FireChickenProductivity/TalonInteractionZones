from talon import ui, canvas, cron, ctrl, actions
from talon.skia import Rect, Image
import os
from .helpers import rgba2hex, verify_home_dir, TRANSPARENT
from .config_parser import parse_zone,is_line_newzone,is_line_endzone
from .settings import *

HOME_DIRECTORY = verify_home_dir()
ZONE_SIZE = 200



class Master:
    def __init__(self) -> None:
        self.displays = {}
        self.showZones = False
        
        # I am not sure about multiple screens here, but it could be theoretically supported
        screens = ui.screens()
        self.screen = screens[0]
        self.screenRect = self.screen.rect.copy()
        self.zonesRect = self.screenRect
        self.canvas = canvas.Canvas.from_screen(self.screen)
        
        self.zones = dict()
        self.configs = dict()
        self.activeID=TRANSPARENT
        
        w=60 if not ZONE_TOGGLE_OVERRIDE_SIZE else ZONE_TOGGLE_OVERRIDE_WIDTH
        h=30 if not ZONE_TOGGLE_OVERRIDE_SIZE else ZONE_TOGGLE_OVERRIDE_HEIGHT
        if ZONE_TOGGLE_OVERRIDE_POSITION:
            self.toggleRect=(Rect(ZONE_TOGGLE_OVERRIDE_X,ZONE_TOGGLE_OVERRIDE_Y,w,h))
        else:
            self.toggleRect=(Rect(self.screen.width/2 - w/2,10,w,h))
        
        self.lastWindowTitle = ""
        self.activeFile = ""
        self.overrideFileName=None
        pass

    def set_zone_override(self,file):
        self.overrideFileName=file

    def enable(self,showZones) -> None:  
        print("Enabling interaction zones")    
        self.canvas.register("draw", self.draw)        
        self.job = cron.interval('16ms', self.update)        
        self.job2 = cron.interval('100ms', self.slow_update)        
        self.canvas.register("mouse", self.on_mouse)
        if showZones:
            self.show()      
    def show(self):
        self.showZones = False
        self.activeFile=""
        self.zones = dict()
        opt = self.get_optimal_file_name()
        s=os.path.join(HOME_DIRECTORY, opt)
        zone_id = 0
        self.color_map = {}
        print("Matched current context to %s" % s)
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
                            self.zones[zone_id]=z
                            z.add_to_map(self.color_map, zone_id)
                            zone_id += 1
                        else:
                            print("Failed to parse zone with config\n%s"%ss)
            
            self.activeFile = opt
            
            print("Passed config parsing stage with %s"%self.activeFile)
            self.showZones = True
        except FileNotFoundError:
            print("Either configuration file txt or image png not found (%s)."%s)
            return
            
    def disable(self) -> None:        
        self.canvas.unregister("draw", self.draw) 
        self.canvas.unregister("mouse", self.on_mouse)
        cron.cancel(self.job)
        cron.cancel(self.job2)
        self.canvas.blocks_mouse = False
    def hide(self):
        self.deactivate_zones()
        self.showZones = False        
        self.canvas.blocks_mouse = False
       
    def deactivate_zones(self):
        if not self.showZones:
            return
        for c in self.zones:
            self.zones[c].deactivate()
        self.canvas.blocks_mouse = False
        
    def draw(self, canvas) -> None:  
        x, y = ctrl.mouse_pos()
        
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
        #canvas.draw_image(self.img, 0,0)
        
        for c in self.zones:
            self.zones[c].draw(canvas)
        pass
    
    def on_mouse(self, event):
        x, y = ctrl.mouse_pos()  
            
        if TOGGLE_ZONE_ENABLED and event.event=="mouseup" and self.toggleRect.contains(x,y):
            self.toggle_showing()
        
        if not self.showZones:
            return
        
        id = self.activeID
        if event.event=="mouseup" and id != TRANSPARENT:
            self.zones[id].click()
            pass

    def toggle_showing(self):
        if not self.showZones:
            self.show()
        else:
            self.hide()
    
    def update(self):   
        x, y = ctrl.mouse_pos()   
        
        block = False   
        
        if TOGGLE_ZONE_ENABLED and self.toggleRect.contains(x,y):
            block = True
             
        if self.showZones:        
            colorID = self.get_active_zone_id()
            #if colorID!=None:
            self.activeID=colorID
            
            if self.activeID != TRANSPARENT and self.activeID is not None:
                block = True
                
            for zoneID in self.zones:
                isHovering = zoneID==self.activeID
                self.zones[zoneID].update(isHovering)
                
        self.canvas.blocks_mouse = block
            
        pass

    def slow_update(self):
        if not self.showZones:
            return
        t = self.get_active_window_title()
        if self.activeFile != self.get_optimal_file_name():
            self.hide()
            self.show()
        if t != self.lastWindowTitle:
           self.set_zone_override(None)
        self.lastWindowTitle = t
        pass
    
    def get_active_zone_id(self):
        x, y = ctrl.mouse_pos() 
        if not self.zonesRect.contains(x,y):
            return TRANSPARENT
        color = self.color_map.get((x,y), TRANSPARENT)
        
        
        if color not in self.zones:
            #print("There is no config matching %s!"%color) 
            return None         
              
                
        return color
      
    def get_optimal_file_name(self):
        validFiles = list()
        for file in os.listdir(HOME_DIRECTORY):
            if file.endswith(".png"):
                validFiles.append(file[:len(file)-4])
        
        if self.overrideFileName != None:
            if self.overrideFileName not in validFiles:
                print("Failed to find '%s', keeping default."%self.overrideFileName)
                self.overrideFileName=None
                return self.get_optimal_file_name()
            return self.overrideFileName
                
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
    
def primative_interaction(action:str):
    """All interactions ever fired are fired here."""
    global master
    try:
        if action[:5]=="bind:":
            actions.user.keybinder_add_key_bind(action[6:].replace('\n',''))
            pass
        elif action[:7]=="unbind:":
            actions.user.keybinder_remove_key_bind(action[8:].replace('\n',''))
        elif action[:5]=="swap:":
            if (master==None):
                print("Null master, please restart talon or report a bug if this persists.")
            master.set_zone_override(action[6:].replace('\n',''))
        elif action[:6]=="start:":
            os.startfile(action[7:].replace('\n',''))
        elif action[:12]=="scroll down:":
           actions.user.mouse_scroll_down(float(action[13:].replace('\n','')))     
        elif action[:10]=="scroll up:":
           actions.user.mouse_scroll_up(float(action[11:].replace('\n','')))
        elif action[:6]=="mimic:": # Not recommended for usage generally (can cause unexpected behaviour)
            actions.user.engine_mimic(action[7:].replace('\n',''))
        else:
            actions.key(action)
    except ValueError:
        actions.insert(action)
    except Exception as e:
        print(str(e))

def toggle_showing():
    global master
    master.toggle_showing()
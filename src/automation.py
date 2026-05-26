# Implements: design/automation_wrapper.md
"""
Automation Wrapper for the Virtual Monitor MCP Server.
Converts logical commands and coordinates to physical OS commands via PyAutoGUI or VNC.
Includes coordinate transformation, execution guard, and thread-safe sequencing.
"""

import time
import logging
import threading
import pyautogui

# Set pyautogui fail-safe (moves mouse to top-left to abort)
pyautogui.FAILSAFE = True

# PyAutoGUI to VNC keysym mapping
PYAUTOGUI_TO_VNC_KEYS = {
    'backspace': 'BackSpace',
    'tab': 'Tab',
    'enter': 'Return',
    'return': 'Return',
    'esc': 'Escape',
    'escape': 'Escape',
    'space': 'space',
    'up': 'Up',
    'down': 'Down',
    'left': 'Left',
    'right': 'Right',
    'home': 'Home',
    'end': 'End',
    'pageup': 'Page_Up',
    'pagedown': 'Page_Down',
    'delete': 'Delete',
    'ctrl': 'Ctrl',
    'alt': 'Alt',
    'shift': 'Shift',
    'win': 'Super_L',
    'command': 'Super_L'
}

class AutomationWrapper:
    def __init__(self, config_manager, visual_state_manager, vnc_manager=None):
        self.config = config_manager
        self.visual_state = visual_state_manager
        self.vnc = vnc_manager
        
        # State Monitor
        self.state = "IDLE"  # IDLE, BUSY, ERROR
        self.lock = threading.Lock()
        
        # Set up coordinates transformation resolution config
        self.default_width = self.config.get("display.width", 1280)
        self.default_height = self.config.get("display.height", 800)

    def _resolve_physical_coordinates(self, x, y, mode=None):
        """
        Converts logical or pixel coordinates into physical pixel coordinates.
        Supports normalized coordinate mode (0.0 to 1.0) or absolute pixel mode.
        Clamps values to screen boundaries to prevent errors.
        """
        mode = mode or self.config.get("automation.coordinate_mode", "normalized")
        
        screen_w, screen_h = None, None
        if self.config.get("automation_mode") == "vnc" and self.vnc:
            vnc_size = self.vnc.get_size()
            if vnc_size:
                screen_w, screen_h = vnc_size
        
        if screen_w is None or screen_h is None:
            try:
                screen_w, screen_h = pyautogui.size()
            except Exception:
                logging.warning("Cannot resolve screen size, using default config dimensions.")
                screen_w, screen_h = self.default_width, self.default_height

        if mode == "normalized":
            # Normalize from 0..1 to 0..screen_size
            phys_x = int(float(x) * screen_w)
            phys_y = int(float(y) * screen_h)
        else:
            phys_x = int(x)
            phys_y = int(y)

        # Clamp to display bounds
        phys_x = max(0, min(phys_x, screen_w - 1))
        phys_y = max(0, min(phys_y, screen_h - 1))
        
        return phys_x, phys_y

    def execute_command(self, action_name, *args, **kwargs):
        """
        Thread-safe execution guard. Coordinates the execution flow:
        validation -> coordinate transformation -> action delegation -> result.
        """
        with self.lock:
            self.state = "BUSY"
            try:
                # Execution Guard: basic environment check
                if self.config.get("automation_mode") == "vnc":
                    if not self.vnc or not self.vnc.client:
                        raise RuntimeError("VNC environment is not connected or active.")
                else:
                    try:
                        pyautogui.size()
                    except Exception as e:
                        raise RuntimeError(f"Display environment is not accessible: {e}")

                # Call the corresponding method
                method = getattr(self, f"_action_{action_name}", None)
                if not method:
                    raise ValueError(f"Unknown action: {action_name}")
                
                logging.info(f"Executing automation command: {action_name} with args={args}, kwargs={kwargs}")
                result = method(*args, **kwargs)
                
                self.state = "IDLE"
                return {
                    "success": True,
                    "action": action_name,
                    "result": result
                }
            except Exception as e:
                logging.error(f"Error executing automation action '{action_name}': {e}")
                self.state = "ERROR"
                return {
                    "success": False,
                    "action": action_name,
                    "error": str(e)
                }

    # --- Actions Implementation ---

    def _action_click(self, x, y, button="left", clicks=1, coordinate_mode=None):
        phys_x, phys_y = self._resolve_physical_coordinates(x, y, coordinate_mode)
        if self.config.get("automation_mode") == "vnc":
            self.vnc.mouse_move(phys_x, phys_y)
            btn_code = 0
            if button == "middle": btn_code = 1
            elif button == "right": btn_code = 2
            for _ in range(clicks):
                self.vnc.mouse_click(btn_code)
        else:
            pyautogui.click(x=phys_x, y=phys_y, button=button, clicks=clicks)
        return {"x": phys_x, "y": phys_y}

    def _action_move_to(self, x, y, coordinate_mode=None):
        phys_x, phys_y = self._resolve_physical_coordinates(x, y, coordinate_mode)
        if self.config.get("automation_mode") == "vnc":
            self.vnc.mouse_move(phys_x, phys_y)
        else:
            duration = self.config.get("automation.mouse_speed", 0.1)
            pyautogui.moveTo(x=phys_x, y=phys_y, duration=duration)
        return {"x": phys_x, "y": phys_y}

    def _action_drag_to(self, x, y, button="left", coordinate_mode=None):
        phys_x, phys_y = self._resolve_physical_coordinates(x, y, coordinate_mode)
        if self.config.get("automation_mode") == "vnc":
            btn_code = 0
            if button == "middle": btn_code = 1
            elif button == "right": btn_code = 2
            self.vnc.mouse_down(btn_code)
            self.vnc.mouse_move(phys_x, phys_y)
            self.vnc.mouse_up(btn_code)
        else:
            duration = self.config.get("automation.mouse_speed", 0.1)
            pyautogui.dragTo(x=phys_x, y=phys_y, button=button, duration=duration)
        return {"x": phys_x, "y": phys_y}

    def _action_scroll(self, clicks):
        if self.config.get("automation_mode") == "vnc":
            if clicks > 0:
                self.vnc.mouse_scroll_up(int(clicks))
            elif clicks < 0:
                self.vnc.mouse_scroll_down(abs(int(clicks)))
        else:
            pyautogui.scroll(int(clicks))
        return {"clicks": clicks}

    def _action_type(self, text, interval=0.01, mode="auto"):
        if self.config.get("automation_mode") == "vnc":
            self.vnc.keyboard_write(text)
            return {"method": "vnc_write", "length": len(text)}
        
        is_ascii = all(ord(c) < 128 for c in text)
        if mode == "paste" or (mode == "auto" and (not is_ascii or len(text) > 15 or "\n" in text)):
            import pyperclip
            old_clipboard = ""
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                pass
            
            try:
                pyperclip.copy(text)
                time.sleep(0.05)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.05)
                return {"method": "paste", "length": len(text)}
            finally:
                try:
                    if old_clipboard:
                        pyperclip.copy(old_clipboard)
                except Exception:
                    pass
        else:
            pyautogui.write(text, interval=interval)
            return {"method": "keyboard", "length": len(text)}

    def _action_press(self, key):
        if self.config.get("automation_mode") == "vnc":
            if isinstance(key, list):
                mapped_keys = [PYAUTOGUI_TO_VNC_KEYS.get(k.lower(), k) for k in key]
            else:
                mapped_keys = [PYAUTOGUI_TO_VNC_KEYS.get(key.lower(), key)]
            self.vnc.keyboard_press(*mapped_keys)
        else:
            if isinstance(key, list):
                pyautogui.hotkey(*key)
            else:
                pyautogui.press(key)
        return {"key": key}

    def _action_key_down(self, key):
        if self.config.get("automation_mode") == "vnc":
            self.vnc.keyboard_down(PYAUTOGUI_TO_VNC_KEYS.get(key.lower(), key))
        else:
            pyautogui.keyDown(key)
        return {"key": key}

    def _action_key_up(self, key):
        if self.config.get("automation_mode") == "vnc":
            self.vnc.keyboard_up(PYAUTOGUI_TO_VNC_KEYS.get(key.lower(), key))
        else:
            pyautogui.keyUp(key)
        return {"key": key}

    def _action_mouse_down(self, x, y, button="left", coordinate_mode=None):
        phys_x, phys_y = self._resolve_physical_coordinates(x, y, coordinate_mode)
        if self.config.get("automation_mode") == "vnc":
            self.vnc.mouse_move(phys_x, phys_y)
            btn_code = 0
            if button == "middle": btn_code = 1
            elif button == "right": btn_code = 2
            self.vnc.mouse_down(btn_code)
        else:
            pyautogui.mouseDown(x=phys_x, y=phys_y, button=button)
        return {"x": phys_x, "y": phys_y, "button": button}

    def _action_mouse_up(self, x, y, button="left", coordinate_mode=None):
        phys_x, phys_y = self._resolve_physical_coordinates(x, y, coordinate_mode)
        if self.config.get("automation_mode") == "vnc":
            self.vnc.mouse_move(phys_x, phys_y)
            btn_code = 0
            if button == "middle": btn_code = 1
            elif button == "right": btn_code = 2
            self.vnc.mouse_up(btn_code)
        else:
            pyautogui.mouseUp(x=phys_x, y=phys_y, button=button)
        return {"x": phys_x, "y": phys_y, "button": button}

    def _action_mouse_move(self, x, y, coordinate_mode=None):
        phys_x, phys_y = self._resolve_physical_coordinates(x, y, coordinate_mode)
        if self.config.get("automation_mode") == "vnc":
            self.vnc.mouse_move(phys_x, phys_y)
        else:
            pyautogui.moveTo(x=phys_x, y=phys_y)
        return {"x": phys_x, "y": phys_y}

# Implements: design/automation_wrapper.md
"""
Automation Wrapper for the Virtual Monitor MCP Server.
Converts logical commands and coordinates to physical OS commands via PyAutoGUI.
Includes coordinate transformation, execution guard, and thread-safe sequencing.
"""

import time
import logging
import threading
import pyautogui

# Set pyautogui fail-safe (moves mouse to top-left to abort)
pyautogui.FAILSAFE = True

class AutomationWrapper:
    def __init__(self, config_manager, visual_state_manager):
        self.config = config_manager
        self.visual_state = visual_state_manager
        
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
        
        try:
            screen_w, screen_h = pyautogui.size()
        except Exception:
            logging.warning("PyAutoGUI cannot resolve screen size, using default config dimensions.")
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
                try:
                    pyautogui.size()
                except Exception as e:
                    raise RuntimeError(f"X11 Display environment is not accessible: {e}")

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
        pyautogui.click(x=phys_x, y=phys_y, button=button, clicks=clicks)
        return {"x": phys_x, "y": phys_y}

    def _action_move_to(self, x, y, coordinate_mode=None):
        phys_x, phys_y = self._resolve_physical_coordinates(x, y, coordinate_mode)
        # Smooth mouse speed
        duration = self.config.get("automation.mouse_speed", 0.1)
        pyautogui.moveTo(x=phys_x, y=phys_y, duration=duration)
        return {"x": phys_x, "y": phys_y}

    def _action_drag_to(self, x, y, button="left", coordinate_mode=None):
        phys_x, phys_y = self._resolve_physical_coordinates(x, y, coordinate_mode)
        duration = self.config.get("automation.mouse_speed", 0.1)
        pyautogui.dragTo(x=phys_x, y=phys_y, button=button, duration=duration)
        return {"x": phys_x, "y": phys_y}

    def _action_scroll(self, clicks):
        # clicks can be positive (up) or negative (down)
        pyautogui.scroll(int(clicks))
        return {"clicks": clicks}

    def _action_type(self, text, interval=0.01, mode="auto"):
        # mode can be "keyboard", "paste", or "auto"
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
                time.sleep(0.05)  # Wait for clipboard registration
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.05)  # Wait for paste operation to complete
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
        # key can be single key or list of keys to press sequentially (e.g. 'enter', ['ctrl', 'c'])
        if isinstance(key, list):
            pyautogui.hotkey(*key)
        else:
            pyautogui.press(key)
        return {"key": key}

    def _action_key_down(self, key):
        pyautogui.keyDown(key)
        return {"key": key}

    def _action_key_up(self, key):
        pyautogui.keyUp(key)
        return {"key": key}

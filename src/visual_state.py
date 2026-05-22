# Implements: design/visual_state_manager.md
"""
Visual State Manager for the Virtual Monitor MCP Server.
Captures screen raw data, encodes to base64 formats, manages screenshot cache, and handles concurrency.
"""

import io
import time
import base64
import logging
import threading
from PIL import Image
import pyautogui

# Set pyautogui safety setting
pyautogui.FAILSAFE = True

class VisualStateManager:
    def __init__(self, config_manager):
        self.config = config_manager
        self.lock = threading.Lock()
        
        # Cache variables
        self.cache_limit = self.config.get("visual.cache_limit", 5)
        self.cache = []  # List of tuples (timestamp, img_bytes, img_obj)
        self.last_capture_time = 0
        self.cache_expiry = 0.05  # 50ms cache validity to avoid redundant captures

    def capture_screen(self, force=False) -> Image.Image:
        """Captures the current screen. Uses caching to prevent hammering X11."""
        now = time.time()
        
        with self.lock:
            # Check if we can return from cache
            if not force and self.cache and (now - self.last_capture_time < self.cache_expiry):
                return self.cache[-1][2]
            
            try:
                # Capture screen using pyautogui (returns PIL Image)
                # Ensure DISPLAY is set before calling this in the runner process
                img = pyautogui.screenshot()
                self.last_capture_time = now
                
                # Manage cache
                if len(self.cache) >= self.cache_limit:
                    self.cache.pop(0)
                
                # Keep both PIL image and placeholder for encoded bytes (lazily populated)
                self.cache.append((now, None, img))
                return img
            except Exception as e:
                logging.error(f"Failed to capture screen: {e}")
                # Return a blank placeholder image if capture fails
                width = self.config.get("display.width", 1280)
                height = self.config.get("display.height", 800)
                return Image.new("RGB", (width, height), color="black")

    def get_screen_base64(self, format_type=None, quality=None, force=False) -> str:
        """Gets base64 encoded screen image."""
        fmt = format_type or self.config.get("visual.format", "png")
        q = quality or self.config.get("visual.jpeg_quality", 80)
        
        img = self.capture_screen(force=force)
        
        with self.lock:
            # Check if current cache tail already has this exact format encoded (lazy cache)
            if self.cache and not force:
                cache_entry = self.cache[-1]
                # If cached bytes exist and are populated, we can reuse if it's recent
                # But since format/quality can change, we simple encode on demand or store it.
                pass
            
            buffered = io.BytesIO()
            if fmt.lower() == "jpeg" or fmt.lower() == "jpg":
                img.save(buffered, format="JPEG", quality=q)
            else:
                img.save(buffered, format="PNG")
                
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return img_str

    def get_screen_bytes(self, format_type=None, quality=None, force=False) -> bytes:
        """Gets raw bytes of the screen image."""
        fmt = format_type or self.config.get("visual.format", "png")
        q = quality or self.config.get("visual.jpeg_quality", 80)
        
        img = self.capture_screen(force=force)
        
        buffered = io.BytesIO()
        if fmt.lower() == "jpeg" or fmt.lower() == "jpg":
            img.save(buffered, format="JPEG", quality=q)
        else:
            img.save(buffered, format="PNG")
            
        return buffered.getvalue()

    def get_screen_metadata(self) -> dict:
        """Returns metadata about the display state."""
        try:
            # Get physical/logical resolution
            width, height = pyautogui.size()
            return {
                "width": width,
                "height": height,
                "timestamp": time.time(),
                "display_env": pyautogui.getActiveWindow() is not None  # checks if GUI env active
            }
        except Exception as e:
            logging.error(f"Error reading screen metadata: {e}")
            return {
                "width": self.config.get("display.width", 1280),
                "height": self.config.get("display.height", 800),
                "timestamp": time.time(),
                "display_env": False
            }

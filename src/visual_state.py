# Implements: design/visual_state_manager.md
"""
Visual State Manager for the Virtual Monitor MCP Server.
Captures screen raw data, encodes to base64 formats, manages screenshot cache, and handles concurrency.
Manages physical screenshot file storage with size-based automatic rotation.
"""

import io
import os
import time
import glob
import base64
import logging
import threading
from PIL import Image
import pyautogui

try:
    import mss
except ImportError:
    mss = None

# Set pyautogui safety setting
pyautogui.FAILSAFE = True

class VisualStateManager:
    def __init__(self, config_manager, vnc_manager=None):
        self.config = config_manager
        self.vnc = vnc_manager
        self.lock = threading.Lock()
        
        # Cache variables
        self.cache_limit = self.config.get("visual.cache_limit", 5)
        self.cache = []  # List of tuples (timestamp, img_bytes, img_obj)
        self.last_capture_time = 0
        self.cache_expiry = 0.05  # 50ms cache validity to avoid redundant captures

    def capture_screen(self, force=False) -> Image.Image:
        """Captures the current screen. Uses caching to prevent hammering X11 or VNC."""
        now = time.time()
        
        with self.lock:
            # Check if we can return from cache
            if not force and self.cache and (now - self.last_capture_time < self.cache_expiry):
                return self.cache[-1][2]
            
            try:
                # VNC Mode capture
                if self.config.get("automation_mode") == "vnc" and self.vnc:
                    img = self.vnc.capture_screen()
                else:
                    # Capture screen using mss if available (much faster than pyautogui/scrot), fallback to pyautogui
                    if mss:
                        with mss.mss() as sct:
                            # sct.monitors[1] is the first active monitor, sct.monitors[0] is the bounding box of all monitors
                            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                            sct_img = sct.grab(monitor)
                            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    else:
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
        # VNC Mode
        if self.config.get("automation_mode") == "vnc" and self.vnc:
            vnc_size = self.vnc.get_size()
            if vnc_size:
                return {
                    "width": vnc_size[0],
                    "height": vnc_size[1],
                    "timestamp": time.time(),
                    "display_env": True
                }
            else:
                return {
                    "width": self.config.get("display.width", 1280),
                    "height": self.config.get("display.height", 800),
                    "timestamp": time.time(),
                    "display_env": False
                }
                
        # Local Mode
        try:
            # Get physical/logical resolution
            width, height = pyautogui.size()
            
            display_env = False
            if hasattr(pyautogui, "getActiveWindow"):
                try:
                    display_env = pyautogui.getActiveWindow() is not None
                except Exception:
                    pass

            return {
                "width": width,
                "height": height,
                "timestamp": time.time(),
                "display_env": display_env
            }
        except Exception as e:
            logging.error(f"Error reading screen metadata: {e}")
            return {
                "width": self.config.get("display.width", 1280),
                "height": self.config.get("display.height", 800),
                "timestamp": time.time(),
                "display_env": False
            }

    # --- Screenshot File Capacity Management ---

    def save_screenshot(self, format_type="png", quality=80) -> str:
        """Captures screen and saves it as a file, enforcing storage rotation limits."""
        raw_dir = self.config.get("screenshot.save_dir", "~/.config/vmvm/")
        save_dir = os.path.abspath(os.path.expanduser(raw_dir))
        os.makedirs(save_dir, exist_ok=True)

        img = self.capture_screen(force=True)

        fmt = format_type.lower()
        if fmt not in ("png", "jpeg", "jpg"):
            fmt = "png"

        timestamp = int(time.time() * 1000)
        filename = f"screenshot_{timestamp}.{fmt}"
        file_path = os.path.join(save_dir, filename)

        if fmt == "png":
            img.save(file_path, format="PNG")
        else:
            img.save(file_path, format="JPEG", quality=quality)

        logging.info(f"Saved screenshot to {file_path}")

        # Enforce storage limits
        self._enforce_storage_limit(save_dir)

        return file_path

    def _enforce_storage_limit(self, save_dir):
        """Checks size limit and deletes oldest screenshot files when limit is exceeded."""
        max_mb = self.config.get("screenshot.max_size_mb", 100)
        max_bytes = max_mb * 1024 * 1024

        pattern = os.path.join(save_dir, "screenshot_*")
        files = glob.glob(pattern)

        file_info = []
        for f in files:
            if os.path.isfile(f):
                try:
                    stat = os.stat(f)
                    file_info.append((f, stat.st_size, stat.st_mtime))
                except Exception:
                    pass

        # Sort by modification time (oldest first)
        file_info.sort(key=lambda x: x[2])
        total_size = sum(x[1] for x in file_info)

        deleted = 0
        for fpath, fsize, _ in file_info:
            if total_size <= max_bytes:
                break
            try:
                os.remove(fpath)
                total_size -= fsize
                deleted += 1
            except Exception as e:
                logging.error(f"Failed to delete old screenshot {fpath}: {e}")

        if deleted > 0:
            logging.info(f"Screenshot limit of {max_mb}MB reached. Deleted {deleted} oldest screenshot files.")

    def get_screenshot_storage_stats(self) -> dict:
        """Returns details on screenshot folder size, capacity limits, and file listings."""
        raw_dir = self.config.get("screenshot.save_dir", "~/.config/vmvm/")
        save_dir = os.path.abspath(os.path.expanduser(raw_dir))
        
        max_mb = self.config.get("screenshot.max_size_mb", 100)
        max_bytes = max_mb * 1024 * 1024

        if not os.path.exists(save_dir):
            return {
                "save_dir": save_dir,
                "total_size_bytes": 0,
                "max_size_bytes": max_bytes,
                "max_size_mb": max_mb,
                "files": []
            }

        pattern = os.path.join(save_dir, "screenshot_*")
        files = glob.glob(pattern)

        file_list = []
        total_size = 0
        for f in files:
            if os.path.isfile(f):
                try:
                    stat = os.stat(f)
                    size = stat.st_size
                    total_size += size
                    file_list.append({
                        "name": os.path.basename(f),
                        "size_bytes": size,
                        "created_time": stat.st_mtime
                    })
                except Exception:
                    pass

        # Sort by created time (newest first)
        file_list.sort(key=lambda x: x["created_time"], reverse=True)

        return {
            "save_dir": save_dir,
            "total_size_bytes": total_size,
            "max_size_bytes": max_bytes,
            "max_size_mb": max_mb,
            "files": file_list
        }

    def clear_all_screenshots(self) -> int:
        """Deletes all screenshot_* files from save_dir and returns deleted count."""
        raw_dir = self.config.get("screenshot.save_dir", "~/.config/vmvm/")
        save_dir = os.path.abspath(os.path.expanduser(raw_dir))
        
        if not os.path.exists(save_dir):
            return 0

        pattern = os.path.join(save_dir, "screenshot_*")
        files = glob.glob(pattern)

        deleted = 0
        for f in files:
            if os.path.isfile(f):
                try:
                    os.remove(f)
                    deleted += 1
                except Exception as e:
                    logging.error(f"Failed to delete {f}: {e}")
        
        logging.info(f"Cleared all {deleted} screenshot files from {save_dir}.")
        return deleted

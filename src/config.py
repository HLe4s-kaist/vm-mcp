# Implements: design/main.md (Section 2.5 Configuration Manager)
"""
Configuration Manager for the Virtual Monitor MCP Server.
Manages loading, updating, and saving system configurations in a centralized JSON file.
"""

import os
import json
import logging

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/vmvm/config.json")
DEFAULT_CONFIG = {
    "automation_mode": "local",  # 'local' or 'vnc'
    "display": {
        "width": 1280,
        "height": 800,
        "color_depth": 24,
        "display_num": 99
    },
    "mcp": {
        "transport": "stdio",  # 'stdio' or 'sse'
        "port": 8001,
        "host": "0.0.0.0"
    },
    "vnc": {
        "host": "127.0.0.1",
        "port": 5900,
        "password": "",
        "shared": True
    },
    "automation": {
        "fail_safe": True,
        "mouse_speed": 0.1,  # in seconds (pyautogui.MINIMUM_DURATION)
        "coordinate_mode": "normalized"  # 'normalized' (0..1) or 'pixel'
    },
    "visual": {
        "cache_limit": 5,
        "format": "png",  # 'png' or 'jpeg'
        "jpeg_quality": 80
    },
    "screenshot": {
        "save_dir": "~/.config/vmvm/screenshot/",
        "max_size_mb": 100
    },
    "monitoring": {
        "enabled": True,
        "host": "0.0.0.0",
        "port": 8080,
        "framerate": 5,
        "password": ""
    }
}

class ConfigurationManager:
    def __init__(self, config_path=None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = {}
        self.load()

    def load(self):
        """Loads configuration from the file system, fallback to default if not exists."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    self.config = self._merge_dicts(DEFAULT_CONFIG, user_config)
                logging.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logging.error(f"Error loading configuration from {self.config_path}: {e}. Using defaults.")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()
            self.save()  # Write default config to file

    def save(self):
        """Saves current configuration to the config file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logging.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logging.error(f"Failed to save configuration to {self.config_path}: {e}")

    def get(self, key_path, default=None):
        """Retrieves a configuration value using dot notation, e.g., 'display.width'."""
        keys = key_path.split(".")
        val = self.config
        for key in keys:
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                return default
        return val

    def set(self, key_path, value, save=True):
        """Sets a configuration value using dot notation and optionally saves it to file."""
        keys = key_path.split(".")
        val = self.config
        for key in keys[:-1]:
            if key not in val or not isinstance(val[key], dict):
                val[key] = {}
            val = val[key]
        val[keys[-1]] = value
        if save:
            self.save()

    def _merge_dicts(self, default, user):
        """Recursively merges user config dict into default config dict."""
        merged = default.copy()
        for k, v in user.items():
            if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k] = self._merge_dicts(merged[k], v)
            else:
                merged[k] = v
        return merged

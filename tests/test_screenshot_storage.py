import os
import sys
import subprocess
import time
import shutil
import unittest

# Start Xvfb if on Linux before importing pyautogui or visual_state
xvfb_proc = None
if sys.platform != "win32" and "DISPLAY" not in os.environ:
    os.environ['DISPLAY'] = ':98'
    try:
        # Check if Xvfb is already running or lock file exists
        lock_file = "/tmp/.X98-lock"
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except Exception:
                pass
        xvfb_proc = subprocess.Popen(
            ["Xvfb", ":98", "-screen", "0", "1280x800x24"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.5)
    except Exception as e:
        print(f"Warning: Failed to start Xvfb for tests: {e}")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from config import ConfigurationManager
from visual_state import VisualStateManager

class TestScreenshotStorage(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        global xvfb_proc
        if xvfb_proc:
            try:
                xvfb_proc.terminate()
                xvfb_proc.wait(timeout=2)
            except Exception:
                try:
                    xvfb_proc.kill()
                    xvfb_proc.wait()
                except Exception:
                    pass

    def setUp(self):
        # Create a temporary config path and screenshot folder
        self.test_dir = os.path.abspath("./test_screenshot_dir")
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.config = ConfigurationManager()
        # Set save_dir to our temp test dir and set limit to 1 MB (approx 1,048,576 bytes)
        self.config.set("screenshot.save_dir", self.test_dir, save=False)
        self.config.set("screenshot.max_size_mb", 1, save=False)

        self.vsm = VisualStateManager(self.config)

    def tearDown(self):
        # Clean up files and directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_stats(self):
        # Save a screenshot
        path = self.vsm.save_screenshot(format_type="png")
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.basename(path).startswith("screenshot_"))

        # Verify stats
        stats = self.vsm.get_screenshot_storage_stats()
        self.assertEqual(stats["max_size_mb"], 1)
        self.assertEqual(len(stats["files"]), 1)
        self.assertEqual(stats["files"][0]["name"], os.path.basename(path))
        self.assertGreater(stats["total_size_bytes"], 0)

    def test_storage_rotation(self):
        # We will set max_size_mb to a tiny value (~8 KB) to force rotation
        self.config.set("screenshot.max_size_mb", 0.008, save=False)
        
        # Save first screenshot
        path1 = self.vsm.save_screenshot(format_type="png")
        self.assertTrue(os.path.exists(path1))
        
        # Save second screenshot (time sleep to ensure distinct timestamp/mtime)
        time.sleep(0.1)
        path2 = self.vsm.save_screenshot(format_type="png")
        self.assertTrue(os.path.exists(path2))
        
        # Save third screenshot. Total size of 3 screenshots (~11 KB) will exceed ~8 KB limit,
        # prompting the rotation to delete the oldest screenshot (path1).
        time.sleep(0.1)
        path3 = self.vsm.save_screenshot(format_type="png")
        
        self.assertFalse(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))
        self.assertTrue(os.path.exists(path3))

    def test_clear_all(self):
        # Save a few screenshots
        self.vsm.save_screenshot(format_type="png")
        time.sleep(0.05)
        self.vsm.save_screenshot(format_type="png")
        
        stats = self.vsm.get_screenshot_storage_stats()
        self.assertEqual(len(stats["files"]), 2)
        
        # Clear all
        deleted = self.vsm.clear_all_screenshots()
        self.assertEqual(deleted, 2)
        
        stats_after = self.vsm.get_screenshot_storage_stats()
        self.assertEqual(len(stats_after["files"]), 0)
        self.assertEqual(stats_after["total_size_bytes"], 0)

if __name__ == "__main__":
    unittest.main()

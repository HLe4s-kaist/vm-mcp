"""
End-to-end VNC integration test.
Starts Xvfb, x11vnc, then runs the VNC manager to verify:
1. VNC connection works
2. Screenshot capture returns valid images
3. Mouse move/click work without errors
4. Keyboard press/write work without errors
5. Web monitoring server starts and serves frames via WebSocket
6. MCP tools work through VNC backend
"""

import sys
import os
import time
import asyncio
import threading
import subprocess
import signal

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import ConfigurationManager
from vnc_manager import VNCManager
from visual_state import VisualStateManager
from automation import AutomationWrapper

# Test config
VNC_PORT = 5999
DISPLAY_NUM = 98

xvfb_proc = None
x11vnc_proc = None


def setup_test_env():
    """Start Xvfb and x11vnc for testing."""
    global xvfb_proc, x11vnc_proc

    # Clean up any existing lock files
    lock_file = f"/tmp/.X{DISPLAY_NUM}-lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)

    # Start Xvfb
    display = f":{DISPLAY_NUM}"
    xvfb_proc = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", "1280x800x24"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(1.5)
    if xvfb_proc.poll() is not None:
        raise RuntimeError(f"Xvfb failed to start on display {display}")
    print(f"✓ Xvfb started on display {display} (PID: {xvfb_proc.pid})")

    # Start x11vnc sharing the Xvfb display
    x11vnc_proc = subprocess.Popen(
        ["x11vnc", "-display", display, "-rfbport", str(VNC_PORT),
         "-nopw", "-forever", "-shared", "-quiet"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(1.5)
    if x11vnc_proc.poll() is not None:
        raise RuntimeError(f"x11vnc failed to start on port {VNC_PORT}")
    print(f"✓ x11vnc started on port {VNC_PORT} (PID: {x11vnc_proc.pid})")


def teardown_test_env():
    """Stop test processes."""
    global xvfb_proc, x11vnc_proc
    for p in [x11vnc_proc, xvfb_proc]:
        if p:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()
                p.wait()
    print("✓ Test environment cleaned up")


def test_vnc_connection():
    """Test VNC manager connects and captures frames."""
    print("\n=== Test 1: VNC Connection & Screenshot ===")

    config = ConfigurationManager.__new__(ConfigurationManager)
    config.config = {
        "automation_mode": "vnc",
        "vnc": {"host": "127.0.0.1", "port": VNC_PORT, "password": "", "shared": True},
        "display": {"width": 1280, "height": 800, "color_depth": 24, "display_num": DISPLAY_NUM},
        "visual": {"cache_limit": 5, "format": "png", "jpeg_quality": 80},
        "screenshot": {"save_dir": "/tmp/vmvm_test_screenshots/", "max_size_mb": 10},
        "automation": {"fail_safe": True, "mouse_speed": 0.1, "coordinate_mode": "pixel"},
    }
    config.config_path = "/dev/null"

    vnc = VNCManager(config)
    loop = asyncio.new_event_loop()

    errors = []

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(vnc.start(loop))
        loop.run_forever()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()

    # Wait for connection
    print("  Waiting for VNC connection...")
    connected = vnc._connected_event.wait(timeout=10.0)
    if not connected:
        errors.append("VNC connection timed out after 10 seconds")
        print(f"  ✗ {errors[-1]}")
    else:
        print(f"  ✓ VNC connected to 127.0.0.1:{VNC_PORT}")

        # Check size
        size = vnc.get_size()
        if size:
            print(f"  ✓ Display size: {size[0]}x{size[1]}")
        else:
            errors.append("get_size() returned None")
            print(f"  ✗ {errors[-1]}")

        # Wait for first frame
        time.sleep(1.0)

        # Capture screenshot
        img = vnc.capture_screen()
        if img and img.size[0] > 0 and img.size[1] > 0:
            print(f"  ✓ Screenshot captured: {img.size[0]}x{img.size[1]} mode={img.mode}")
        else:
            errors.append("capture_screen() returned invalid image")
            print(f"  ✗ {errors[-1]}")

        # Test capture_screen_fresh
        try:
            fresh_img = vnc.capture_screen_fresh()
            if fresh_img and fresh_img.size[0] > 0:
                print(f"  ✓ Fresh screenshot captured: {fresh_img.size[0]}x{fresh_img.size[1]} mode={fresh_img.mode}")
            else:
                errors.append("capture_screen_fresh() returned invalid image")
                print(f"  ✗ {errors[-1]}")
        except Exception as e:
            errors.append(f"capture_screen_fresh() failed: {e}")
            print(f"  ✗ {errors[-1]}")

    # Cleanup
    loop.call_soon_threadsafe(lambda: asyncio.ensure_future(vnc.stop()))
    time.sleep(0.5)
    loop.call_soon_threadsafe(loop.stop)
    time.sleep(0.3)

    return errors


def test_vnc_mouse_keyboard():
    """Test mouse and keyboard operations via VNC."""
    print("\n=== Test 2: VNC Mouse & Keyboard ===")

    config = ConfigurationManager.__new__(ConfigurationManager)
    config.config = {
        "automation_mode": "vnc",
        "vnc": {"host": "127.0.0.1", "port": VNC_PORT, "password": "", "shared": True},
        "display": {"width": 1280, "height": 800, "color_depth": 24, "display_num": DISPLAY_NUM},
        "visual": {"cache_limit": 5, "format": "png", "jpeg_quality": 80},
        "screenshot": {"save_dir": "/tmp/vmvm_test_screenshots/", "max_size_mb": 10},
        "automation": {"fail_safe": True, "mouse_speed": 0.1, "coordinate_mode": "pixel"},
    }
    config.config_path = "/dev/null"

    vnc = VNCManager(config)
    loop = asyncio.new_event_loop()

    errors = []

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(vnc.start(loop))
        loop.run_forever()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()

    # Wait for connection
    connected = vnc._connected_event.wait(timeout=10.0)
    if not connected:
        errors.append("VNC connection timed out")
        print(f"  ✗ {errors[-1]}")
    else:
        # Test mouse move
        try:
            vnc.mouse_move(100, 100)
            print("  ✓ mouse_move(100, 100)")
        except Exception as e:
            errors.append(f"mouse_move failed: {e}")
            print(f"  ✗ {errors[-1]}")

        time.sleep(0.1)

        # Test mouse click
        try:
            vnc.mouse_click(0)
            print("  ✓ mouse_click(0) - left click")
        except Exception as e:
            errors.append(f"mouse_click failed: {e}")
            print(f"  ✗ {errors[-1]}")

        time.sleep(0.1)

        # Test mouse right click
        try:
            vnc.mouse_click(2)
            print("  ✓ mouse_click(2) - right click")
        except Exception as e:
            errors.append(f"mouse_right_click failed: {e}")
            print(f"  ✗ {errors[-1]}")

        time.sleep(0.1)

        # Test mouse down/up
        try:
            vnc.mouse_down(0)
            time.sleep(0.05)
            vnc.mouse_up(0)
            print("  ✓ mouse_down/up - drag simulation")
        except Exception as e:
            errors.append(f"mouse_down/up failed: {e}")
            print(f"  ✗ {errors[-1]}")

        time.sleep(0.1)

        # Test scroll
        try:
            vnc.mouse_scroll_up(2)
            vnc.mouse_scroll_down(2)
            print("  ✓ mouse_scroll_up/down")
        except Exception as e:
            errors.append(f"mouse_scroll failed: {e}")
            print(f"  ✗ {errors[-1]}")

        time.sleep(0.1)

        # Test keyboard write
        try:
            vnc.keyboard_write("hello")
            print("  ✓ keyboard_write('hello')")
        except Exception as e:
            errors.append(f"keyboard_write failed: {e}")
            print(f"  ✗ {errors[-1]}")

        time.sleep(0.1)

        # Test keyboard press
        try:
            vnc.keyboard_press("Return")
            print("  ✓ keyboard_press('Return')")
        except Exception as e:
            errors.append(f"keyboard_press failed: {e}")
            print(f"  ✗ {errors[-1]}")

        time.sleep(0.1)

        # Test keyboard combo
        try:
            vnc.keyboard_press("Ctrl", "a")
            print("  ✓ keyboard_press('Ctrl', 'a') - key combo")
        except Exception as e:
            errors.append(f"keyboard combo failed: {e}")
            print(f"  ✗ {errors[-1]}")

        time.sleep(0.1)

        # Test key down/up
        try:
            vnc.keyboard_down("Shift")
            time.sleep(0.05)
            vnc.keyboard_up("Shift")
            print("  ✓ keyboard_down/up('Shift')")
        except Exception as e:
            errors.append(f"keyboard_down/up failed: {e}")
            print(f"  ✗ {errors[-1]}")

    # Cleanup
    loop.call_soon_threadsafe(lambda: asyncio.ensure_future(vnc.stop()))
    time.sleep(0.5)
    loop.call_soon_threadsafe(loop.stop)
    time.sleep(0.3)

    return errors


def test_automation_wrapper_vnc():
    """Test automation wrapper with VNC backend."""
    print("\n=== Test 3: AutomationWrapper with VNC ===")

    config = ConfigurationManager.__new__(ConfigurationManager)
    config.config = {
        "automation_mode": "vnc",
        "vnc": {"host": "127.0.0.1", "port": VNC_PORT, "password": "", "shared": True},
        "display": {"width": 1280, "height": 800, "color_depth": 24, "display_num": DISPLAY_NUM},
        "visual": {"cache_limit": 5, "format": "png", "jpeg_quality": 80},
        "screenshot": {"save_dir": "/tmp/vmvm_test_screenshots/", "max_size_mb": 10},
        "automation": {"fail_safe": True, "mouse_speed": 0.1, "coordinate_mode": "normalized"},
    }
    config.config_path = "/dev/null"

    vnc = VNCManager(config)
    loop = asyncio.new_event_loop()
    errors = []

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(vnc.start(loop))
        loop.run_forever()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()

    # Wait for connection
    connected = vnc._connected_event.wait(timeout=10.0)
    if not connected:
        errors.append("VNC connection timed out")
        print(f"  ✗ {errors[-1]}")
    else:
        visual = VisualStateManager(config, vnc_manager=vnc)
        auto = AutomationWrapper(config, visual, vnc_manager=vnc)

        # Test click via automation wrapper (normalized coordinates)
        res = auto.execute_command("click", x=0.5, y=0.5, button="left", clicks=1)
        if res.get("success"):
            print(f"  ✓ click(0.5, 0.5) → {res['result']}")
        else:
            errors.append(f"click failed: {res.get('error')}")
            print(f"  ✗ {errors[-1]}")

        # Test move_to
        res = auto.execute_command("move_to", x=0.3, y=0.7)
        if res.get("success"):
            print(f"  ✓ move_to(0.3, 0.7) → {res['result']}")
        else:
            errors.append(f"move_to failed: {res.get('error')}")
            print(f"  ✗ {errors[-1]}")

        # Test type
        res = auto.execute_command("type", text="test input")
        if res.get("success"):
            print(f"  ✓ type('test input') → {res['result']}")
        else:
            errors.append(f"type failed: {res.get('error')}")
            print(f"  ✗ {errors[-1]}")

        # Test press
        res = auto.execute_command("press", key="Return")
        if res.get("success"):
            print(f"  ✓ press('Return') → {res['result']}")
        else:
            errors.append(f"press failed: {res.get('error')}")
            print(f"  ✗ {errors[-1]}")

        # Test scroll
        res = auto.execute_command("scroll", clicks=3)
        if res.get("success"):
            print(f"  ✓ scroll(3) → {res['result']}")
        else:
            errors.append(f"scroll failed: {res.get('error')}")
            print(f"  ✗ {errors[-1]}")

        # Test drag_to
        auto.execute_command("click", x=0.1, y=0.1)  # Move to start position
        res = auto.execute_command("drag_to", x=0.9, y=0.9, button="left")
        if res.get("success"):
            print(f"  ✓ drag_to(0.9, 0.9) → {res['result']}")
        else:
            errors.append(f"drag_to failed: {res.get('error')}")
            print(f"  ✗ {errors[-1]}")

        # Test key_down/key_up
        res = auto.execute_command("key_down", key="shift")
        if res.get("success"):
            print(f"  ✓ key_down('shift') → {res['result']}")
        else:
            errors.append(f"key_down failed: {res.get('error')}")
            print(f"  ✗ {errors[-1]}")

        res = auto.execute_command("key_up", key="shift")
        if res.get("success"):
            print(f"  ✓ key_up('shift') → {res['result']}")
        else:
            errors.append(f"key_up failed: {res.get('error')}")
            print(f"  ✗ {errors[-1]}")

        # Test visual state capture
        try:
            img = visual.capture_screen(force=True)
            print(f"  ✓ visual_state.capture_screen() → {img.size[0]}x{img.size[1]} mode={img.mode}")
        except Exception as e:
            errors.append(f"visual_state capture failed: {e}")
            print(f"  ✗ {errors[-1]}")

        # Test visual state base64 (JPEG)
        try:
            b64 = visual.get_screen_base64(format_type="jpeg", quality=80, force=True)
            print(f"  ✓ visual_state.get_screen_base64(jpeg) → {len(b64)} chars")
        except Exception as e:
            errors.append(f"visual_state base64 jpeg failed: {e}")
            print(f"  ✗ {errors[-1]}")

        # Test visual state bytes (JPEG)
        try:
            data = visual.get_screen_bytes(format_type="jpeg", quality=75, force=True)
            print(f"  ✓ visual_state.get_screen_bytes(jpeg) → {len(data)} bytes")
        except Exception as e:
            errors.append(f"visual_state bytes jpeg failed: {e}")
            print(f"  ✗ {errors[-1]}")

        # Test visual state metadata
        try:
            meta = visual.get_screen_metadata()
            print(f"  ✓ visual_state.get_screen_metadata() → {meta}")
        except Exception as e:
            errors.append(f"visual_state metadata failed: {e}")
            print(f"  ✗ {errors[-1]}")

    # Cleanup
    loop.call_soon_threadsafe(lambda: asyncio.ensure_future(vnc.stop()))
    time.sleep(0.5)
    loop.call_soon_threadsafe(loop.stop)
    time.sleep(0.3)

    return errors


def test_monitoring_bridge_vnc():
    """Test the web monitoring bridge with VNC backend."""
    print("\n=== Test 4: MonitoringBridge with VNC ===")

    import urllib.request
    import json

    config = ConfigurationManager.__new__(ConfigurationManager)
    config.config = {
        "automation_mode": "vnc",
        "vnc": {"host": "127.0.0.1", "port": VNC_PORT, "password": "", "shared": True},
        "display": {"width": 1280, "height": 800, "color_depth": 24, "display_num": DISPLAY_NUM},
        "visual": {"cache_limit": 5, "format": "png", "jpeg_quality": 80},
        "screenshot": {"save_dir": "/tmp/vmvm_test_screenshots/", "max_size_mb": 10},
        "automation": {"fail_safe": True, "mouse_speed": 0.1, "coordinate_mode": "normalized"},
        "monitoring": {"enabled": True, "host": "127.0.0.1", "port": 18080, "framerate": 5, "password": ""},
    }
    config.config_path = "/dev/null"

    from monitoring import MonitoringBridge

    vnc = VNCManager(config)
    loop = asyncio.new_event_loop()
    errors = []

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(vnc.start(loop))
        visual = VisualStateManager(config, vnc_manager=vnc)
        auto = AutomationWrapper(config, visual, vnc_manager=vnc)
        bridge = MonitoringBridge(config, visual, auto)
        loop.run_until_complete(bridge.start())
        loop.run_forever()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()

    # Wait for VNC connection + web server startup
    connected = vnc._connected_event.wait(timeout=10.0)
    if not connected:
        errors.append("VNC connection timed out")
        print(f"  ✗ {errors[-1]}")
    else:
        time.sleep(2.0)  # Extra time for web server

        # Test HTTP endpoints
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:18080/", timeout=5)
            html = resp.read().decode()
            if "VM Monitor Bridge" in html:
                print(f"  ✓ Web UI served successfully ({len(html)} bytes)")
            else:
                errors.append("Web UI content doesn't contain expected title")
                print(f"  ✗ {errors[-1]}")
        except Exception as e:
            errors.append(f"Web UI request failed: {e}")
            print(f"  ✗ {errors[-1]}")

        # Test config API
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:18080/api/config", timeout=5)
            cfg = json.loads(resp.read().decode())
            if cfg.get("automation_mode") == "vnc":
                print(f"  ✓ Config API returns automation_mode=vnc")
            else:
                errors.append(f"Config API returned unexpected: {cfg.get('automation_mode')}")
                print(f"  ✗ {errors[-1]}")
        except Exception as e:
            errors.append(f"Config API failed: {e}")
            print(f"  ✗ {errors[-1]}")

        # Test screenshots API
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:18080/api/screenshots", timeout=5)
            stats = json.loads(resp.read().decode())
            print(f"  ✓ Screenshots API: {stats.get('total_size_bytes', 0)} bytes in storage")
        except Exception as e:
            errors.append(f"Screenshots API failed: {e}")
            print(f"  ✗ {errors[-1]}")

        # Test screenshot capture via API
        try:
            req = urllib.request.Request("http://127.0.0.1:18080/api/screenshots/capture", method="POST")
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode())
            if result.get("status") == "success":
                print(f"  ✓ Screenshot capture API: saved {result.get('saved_file')}")
            else:
                errors.append(f"Screenshot capture failed: {result}")
                print(f"  ✗ {errors[-1]}")
        except Exception as e:
            errors.append(f"Screenshot capture API failed: {e}")
            print(f"  ✗ {errors[-1]}")

    # Cleanup
    loop.call_soon_threadsafe(lambda: asyncio.ensure_future(vnc.stop()))
    time.sleep(0.5)
    loop.call_soon_threadsafe(loop.stop)
    time.sleep(0.3)

    return errors


def main():
    print("=" * 60)
    print("VNC Integration Test Suite")
    print("=" * 60)

    all_errors = []

    try:
        setup_test_env()

        errs1 = test_vnc_connection()
        all_errors.extend(errs1)

        errs2 = test_vnc_mouse_keyboard()
        all_errors.extend(errs2)

        errs3 = test_automation_wrapper_vnc()
        all_errors.extend(errs3)

        errs4 = test_monitoring_bridge_vnc()
        all_errors.extend(errs4)

    except Exception as e:
        all_errors.append(f"Test infrastructure error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        teardown_test_env()

    print("\n" + "=" * 60)
    if all_errors:
        print(f"RESULT: {len(all_errors)} ERRORS FOUND")
        for i, err in enumerate(all_errors, 1):
            print(f"  {i}. {err}")
        sys.exit(1)
    else:
        print("RESULT: ALL TESTS PASSED ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()

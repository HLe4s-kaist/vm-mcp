"""
VNC Manager for the Virtual Monitor MCP Server.
Manages asyncvnc-based VNC connections, screen capture, and remote input control.

Key design decisions:
- asyncvnc Mouse/Keyboard methods (move, click, press, write) are SYNCHRONOUS
  and write directly to the asyncio StreamWriter. They must be called from
  the event loop thread, not from arbitrary threads.
- Client.screenshot() is an ASYNC coroutine that refreshes and waits for
  a complete video frame update.
- We use call_soon_threadsafe + futures to bridge sync callers (automation,
  monitoring) to the async event loop safely.
"""

import asyncio
import logging
import threading
import concurrent.futures
from PIL import Image

try:
    import asyncvnc
except ImportError:
    asyncvnc = None


class VNCManager:
    def __init__(self, config_manager):
        self.config = config_manager
        self.client = None
        self.running = False
        self.loop = None
        self.latest_frame = None
        self.lock = threading.Lock()
        self._conn_task = None
        self._connected_event = threading.Event()

    async def start(self, loop):
        """Starts the background VNC connection task."""
        if not asyncvnc:
            logging.error("asyncvnc is not installed. VNC mode will not work.")
            return

        self.loop = loop
        self.running = True
        self._conn_task = self.loop.create_task(self._connection_loop())
        logging.info("VNCManager background connection loop started.")

    async def stop(self):
        """Stops the background VNC connection and cleans up."""
        self.running = False
        self._connected_event.clear()
        if self._conn_task:
            self._conn_task.cancel()
            try:
                await self._conn_task
            except asyncio.CancelledError:
                pass
        self.client = None
        logging.info("VNCManager stopped.")

    @property
    def is_connected(self):
        """Returns True if VNC client is connected."""
        return self.client is not None and self.running

    async def _connection_loop(self):
        """Runs the persistent connection and frame retrieval loop."""
        while self.running:
            host = self.config.get("vnc.host", "127.0.0.1")
            port = int(self.config.get("vnc.port", 5900))
            password = self.config.get("vnc.password", "")
            shared = self.config.get("vnc.shared", True)
            logging.info(f"VNCManager connecting to VNC server at {host}:{port} (shared={shared})...")

            try:
                async with asyncvnc.connect(host, port, password=password if password else None) as client:
                    logging.info(f"VNCManager connection established to {host}:{port}")
                    self.client = client
                    self._connected_event.set()

                    # Connection is active, pull frames periodically
                    while self.running:
                        try:
                            # Check if the connection's writer transport is still open
                            if client.writer.is_closing():
                                logging.warning("VNC connection writer is closing.")
                                break

                            # screenshot() is async: refreshes framebuffer and waits for update
                            pixels = await asyncio.wait_for(client.screenshot(), timeout=5.0)
                            if pixels is not None:
                                # asyncvnc returns RGBA numpy array
                                img = Image.fromarray(pixels, 'RGBA').convert('RGB')
                                with self.lock:
                                    self.latest_frame = img
                            await asyncio.sleep(1.0 / 60.0)  # Up to 60 FPS capture polling
                        except asyncio.TimeoutError:
                            logging.warning("VNC screenshot timed out, retrying...")
                            continue
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            logging.error(f"Error in VNC frame collection: {e}")
                            break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"VNC connection error: {e}. Retrying in 3 seconds...")

            self.client = None
            self._connected_event.clear()
            if self.running:
                await asyncio.sleep(3)

    def _run_on_loop(self, func, *args):
        """
        Schedules a synchronous function to run on the event loop thread and
        waits for the result. This is required because asyncvnc's Mouse/Keyboard
        methods write directly to StreamWriter which is not thread-safe.

        For sync functions that need to execute on the event loop thread.
        """
        if not self.running or not self.loop:
            raise RuntimeError("VNC Manager is not running.")
        if not self.client:
            raise RuntimeError("VNC Client is not connected to any server.")

        future = concurrent.futures.Future()

        def _callback():
            try:
                result = func(*args)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

        self.loop.call_soon_threadsafe(_callback)
        return future.result(timeout=5.0)

    def _run_coro(self, coro):
        """
        Runs an async coroutine on the event loop and waits for its result.
        For async methods like client.screenshot().
        """
        if not self.running or not self.loop:
            raise RuntimeError("VNC Manager is not running.")
        if not self.client:
            raise RuntimeError("VNC Client is not connected to any server.")

        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=10.0)
        except Exception as e:
            logging.error(f"VNCManager coroutine execution failed: {e}")
            raise

    # --- Size metadata ---
    def get_size(self):
        """Gets VNC server display dimensions."""
        if self.client and self.client.video:
            return self.client.video.width, self.client.video.height
        return None

    # --- Screen Capture ---
    def capture_screen(self) -> Image.Image:
        """Returns the latest screenshot image from the background frame loop."""
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()

        # Fallback to blank placeholder
        w = self.config.get("display.width", 1280)
        h = self.config.get("display.height", 800)
        return Image.new("RGB", (w, h), color="black")

    def capture_screen_fresh(self) -> Image.Image:
        """Takes a fresh screenshot via VNC (async). Falls back to cached frame on failure."""
        try:
            pixels = self._run_coro(
                asyncio.wait_for(self.client.screenshot(), timeout=5.0)
            )
            if pixels is not None:
                img = Image.fromarray(pixels, 'RGBA').convert('RGB')
                with self.lock:
                    self.latest_frame = img
                return img
        except Exception as e:
            logging.warning(f"Fresh VNC screenshot failed: {e}, using cached frame")

        return self.capture_screen()

    # --- Mouse Control ---
    # asyncvnc Mouse methods are SYNCHRONOUS. They write directly to the
    # StreamWriter buffer. We must run them on the event loop thread.

    def mouse_move(self, x: int, y: int):
        self._run_on_loop(self.client.mouse.move, x, y)

    def mouse_click(self, button: int = 0):
        # asyncvnc buttons: 0=left, 1=middle, 2=right
        self._run_on_loop(self.client.mouse.click, button)

    def mouse_down(self, button: int = 0):
        def do_down():
            mask = 1 << button
            self.client.mouse.buttons |= mask
            self.client.mouse._write()
        self._run_on_loop(do_down)

    def mouse_up(self, button: int = 0):
        def do_up():
            mask = 1 << button
            self.client.mouse.buttons &= ~mask
            self.client.mouse._write()
        self._run_on_loop(do_up)

    def mouse_scroll_up(self, clicks: int = 1):
        self._run_on_loop(self.client.mouse.scroll_up, clicks)

    def mouse_scroll_down(self, clicks: int = 1):
        self._run_on_loop(self.client.mouse.scroll_down, clicks)

    # --- Keyboard Control ---
    # asyncvnc Keyboard methods are SYNCHRONOUS.

    def keyboard_write(self, text: str):
        self._run_on_loop(self.client.keyboard.write, text)

    def keyboard_press(self, *keys: str):
        self._run_on_loop(self.client.keyboard.press, *keys)

    def keyboard_down(self, key: str):
        """Press a key down without releasing."""
        def do_down():
            data = asyncvnc.key_codes[key].to_bytes(4, 'big')
            self.client.writer.write(b'\x04\x01\x00\x00' + data)
        self._run_on_loop(do_down)

    def keyboard_up(self, key: str):
        """Release a pressed key."""
        def do_up():
            data = asyncvnc.key_codes[key].to_bytes(4, 'big')
            self.client.writer.write(b'\x04\x00\x00\x00' + data)
        self._run_on_loop(do_up)

import asyncio
import logging
import threading
import time
import sys
from PIL import Image
import numpy as np

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
        if self._conn_task:
            self._conn_task.cancel()
            try:
                await self._conn_task
            except asyncio.CancelledError:
                pass
        logging.info("VNCManager stopped.")

    async def _connection_loop(self):
        """Runs the persistent connection and frame retrieval loop."""
        while self.running:
            host = self.config.get("vnc.host", "127.0.0.1")
            port = int(self.config.get("vnc.port", 5900))
            password = self.config.get("vnc.password", "")
            logging.info(f"VNCManager connecting to VNC server at {host}:{port}...")
            
            try:
                async with asyncvnc.connect(host, port, password=password if password else None) as client:
                    logging.info(f"VNCManager connection established to {host}:{port}")
                    self.client = client
                    
                    # Connection is active, pull frames
                    while self.running and not client.writer.transport.is_closing():
                        try:
                            pixels = await client.screenshot()
                            if pixels is not None:
                                img = Image.fromarray(pixels)
                                with self.lock:
                                    self.latest_frame = img
                            await asyncio.sleep(0.1) # Max ~10 FPS capture polling
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
            if self.running:
                await asyncio.sleep(3)

    def _run_coro(self, coro):
        """Runs a coroutine on the background event loop and waits for its result."""
        if not self.running or not self.loop:
            raise RuntimeError("VNC Manager is not running.")
        if not self.client:
            raise RuntimeError("VNC Client is not connected to any server.")
        
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=5.0)
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
        """Returns the latest screenshot image."""
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        
        # Fallback to blank placeholder
        w = self.config.get("display.width", 1280)
        h = self.config.get("display.height", 800)
        return Image.new("RGB", (w, h), color="black")

    # --- Mouse Control ---
    def mouse_move(self, x: int, y: int):
        self._run_coro(self.client.mouse.move(x, y))

    def mouse_click(self, button: int = 0):
        # asyncvnc buttons: 0=left, 1=middle, 2=right, 3=scroll_up, 4=scroll_down
        self._run_coro(self.client.mouse.click(button))

    def mouse_down(self, button: int = 0):
        async def do_down():
            mask = 1 << button
            self.client.mouse.buttons |= mask
            self.client.mouse._write()
        self._run_coro(do_down())

    def mouse_up(self, button: int = 0):
        async def do_up():
            mask = 1 << button
            self.client.mouse.buttons &= ~mask
            self.client.mouse._write()
        self._run_coro(do_up())

    def mouse_scroll_up(self, clicks: int = 1):
        self._run_coro(self.client.mouse.scroll_up(clicks))

    def mouse_scroll_down(self, clicks: int = 1):
        self._run_coro(self.client.mouse.scroll_down(clicks))

    # --- Keyboard Control ---
    def keyboard_write(self, text: str):
        self._run_coro(self.client.keyboard.write(text))

    def keyboard_press(self, *keys: str):
        self._run_coro(self.client.keyboard.press(*keys))

    def keyboard_down(self, key: str):
        async def do_down():
            data = asyncvnc.key_codes[key].to_bytes(4, 'big')
            self.client.writer.write(b'\x04\x01\x00\x00' + data)
        self._run_coro(do_down())

    def keyboard_up(self, key: str):
        async def do_up():
            data = asyncvnc.key_codes[key].to_bytes(4, 'big')
            self.client.writer.write(b'\x04\x00\x00\x00' + data)
        self._run_coro(do_up())

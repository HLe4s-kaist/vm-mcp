# Implements: design/main.md (Section 2.4 Monitoring Bridge)
"""
Monitoring Bridge for the Virtual Monitor MCP Server.
Provides a real-time web monitoring interface and WebSocket stream using Starlette and Uvicorn.
Allows users to visually monitor and interactively control the virtual monitor.
"""

import os
import json
import asyncio
import logging
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect
import uvicorn

class MonitoringBridge:
    def __init__(self, config_manager, visual_state_manager, automation_wrapper):
        self.config = config_manager
        self.visual_state = visual_state_manager
        self.automation = automation_wrapper
        
        # Load the HTML template
        template_dir = os.path.dirname(os.path.abspath(__file__))
        self.html_path = os.path.join(template_dir, "templates", "index.html")
        
        # Initialize Starlette App
        self.app = Starlette(
            routes=[
                Route("/", self.handle_index),
                Route("/api/config", self.handle_get_config, methods=["GET"]),
                Route("/api/config", self.handle_set_config, methods=["POST"]),
                WebSocketRoute("/ws", self.handle_websocket)
            ]
        )
        self.server_task = None
        self.connections = set()

    async def handle_index(self, request):
        """Serves the interactive web interface."""
        if os.path.exists(self.html_path):
            with open(self.html_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content)
        else:
            return HTMLResponse("<h3>Viewer page template not found</h3>", status_code=404)

    async def handle_get_config(self, request):
        """Returns system configuration as JSON."""
        return JSONResponse(self.config.config)

    async def handle_set_config(self, request):
        """Updates system configuration."""
        try:
            body = await request.json()
            for key, val in body.items():
                self.config.set(key, val)
            return JSONResponse({"status": "success", "config": self.config.config})
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

    async def handle_websocket(self, websocket: WebSocket):
        """Handles visual streaming and interactive remote control input."""
        await websocket.accept()
        self.connections.add(websocket)
        logging.info(f"Viewer client connected. Total viewers: {len(self.connections)}")
        
        # Track framerate for this specific connection
        conn_fps = self.config.get("monitoring.framerate", 5)

        # Worker tasks
        async def stream_frames():
            try:
                while websocket in self.connections:
                    # Capture screen as bytes
                    # Use JPEG format for compression and speed
                    img_bytes = self.visual_state.get_screen_bytes(format_type="jpeg", quality=75)
                    await websocket.send_bytes(img_bytes)
                    await asyncio.sleep(1.0 / conn_fps)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logging.error(f"WebSocket frame streaming error: {e}")

        async def read_commands():
            nonlocal conn_fps
            try:
                while websocket in self.connections:
                    data = await websocket.receive_text()
                    try:
                        cmd = json.loads(data)
                        cmd_type = cmd.get("type")
                        
                        if cmd_type == "click":
                            # Execute click
                            x, y = cmd.get("x"), cmd.get("y")
                            button = cmd.get("button", "left")
                            clicks = cmd.get("clicks", 1)
                            # Run blocking pyautogui command in executor to not block event loop
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None, 
                                lambda: self.automation.execute_command(
                                    "click", x=x, y=y, button=button, clicks=clicks
                                )
                            )
                            
                        elif cmd_type == "press":
                            key = cmd.get("key")
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self.automation.execute_command("press", key=key)
                            )
                            
                        elif cmd_type == "key_down":
                            key = cmd.get("key")
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self.automation.execute_command("key_down", key=key)
                            )
                            
                        elif cmd_type == "key_up":
                            key = cmd.get("key")
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self.automation.execute_command("key_up", key=key)
                            )
                            
                        elif cmd_type == "type":
                            text = cmd.get("text")
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self.automation.execute_command("type", text=text)
                            )
                            
                        elif cmd_type == "mouse_down":
                            x, y = cmd.get("x"), cmd.get("y")
                            button = cmd.get("button", "left")
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self.automation.execute_command("mouse_down", x=x, y=y, button=button)
                            )
                        elif cmd_type == "mouse_up":
                            x, y = cmd.get("x"), cmd.get("y")
                            button = cmd.get("button", "left")
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self.automation.execute_command("mouse_up", x=x, y=y, button=button)
                            )
                        elif cmd_type == "mouse_move":
                            x, y = cmd.get("x"), cmd.get("y")
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self.automation.execute_command("mouse_move", x=x, y=y)
                            )
                        elif cmd_type == "scroll":
                            clicks = cmd.get("clicks", 0)
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self.automation.execute_command("scroll", clicks=clicks)
                            )
                        elif cmd_type == "set_fps":
                            new_fps = int(cmd.get("fps", 5))
                            conn_fps = max(1, min(new_fps, 30))
                            logging.info(f"WebSocket client requested FPS change to {conn_fps}")
                            
                    except json.JSONDecodeError:
                        logging.warning(f"Received malformed JSON from WS: {data}")
                    except Exception as e:
                        logging.error(f"Error handling WS command: {e}")
            except WebSocketDisconnect:
                pass

        # Run frame sender and command receiver concurrently
        try:
            await asyncio.gather(stream_frames(), read_commands())
        finally:
            self.connections.discard(websocket)
            logging.info(f"Viewer client disconnected. Total viewers: {len(self.connections)}")

    async def start(self):
        """Starts the Uvicorn web server."""
        host = self.config.get("monitoring.host", "0.0.0.0")
        port = self.config.get("monitoring.port", 8080)
        
        logging.info(f"Starting Web/WebSocket monitoring server on http://{host}:{port}")
        
        config = uvicorn.Config(app=self.app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)
        self.server_task = asyncio.create_task(server.serve())

    async def stop(self):
        """Stops the monitoring server."""
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
            logging.info("Web/WebSocket monitoring server stopped.")

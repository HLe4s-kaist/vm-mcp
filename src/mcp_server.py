# Implements: design/mcp_server.md
"""
MCP Server for the Virtual Monitor.
Interfaces with the official Python mcp SDK using FastMCP.
Exposes GUI automation tools and screen resources to AI agents.
"""

import sys
import logging
from mcp.server.fastmcp import FastMCP

class MCPServer:
    def __init__(self, config_manager, visual_state_manager, automation_wrapper):
        self.config = config_manager
        self.visual_state = visual_state_manager
        self.automation = automation_wrapper
        
        # Initialize FastMCP Server
        # Set up logging to stderr explicitly to prevent stdout pollution
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr
        )
        
        self.mcp = FastMCP("VirtualMonitor")
        self._register_tools()
        self._register_resources()

    def _register_tools(self):
        """Registers system tools for the AI agent."""
        
        @self.mcp.tool(name="get_screen_metadata")
        def get_screen_metadata() -> str:
            """
            Get metadata about the current display environment, such as
            screen dimensions (width and height), and active display environment status.
            """
            metadata = self.visual_state.get_screen_metadata()
            return f"Display Metadata: {metadata}"

        @self.mcp.tool(name="screenshot")
        def screenshot(format_type: str = "png", quality: int = 80) -> str:
            """
            Take a screenshot of the virtual monitor screen and return it as a Base64-encoded string.
            format_type: 'png' or 'jpeg'
            quality: jpeg compression quality (1-100)
            """
            try:
                base64_data = self.visual_state.get_screen_base64(
                    format_type=format_type, quality=quality, force=True
                )
                return base64_data
            except Exception as e:
                return f"Error capturing screenshot: {str(e)}"

        @self.mcp.tool(name="click")
        def click(x: float, y: float, button: str = "left", clicks: int = 1) -> str:
            """
            Perform a mouse click at logical coordinates (x, y).
            x: logical coordinate from 0.0 (left) to 1.0 (right)
            y: logical coordinate from 0.0 (top) to 1.0 (bottom)
            button: 'left', 'right', or 'middle'
            clicks: number of clicks (e.g., 2 for double click)
            """
            res = self.automation.execute_command(
                "click", x=x, y=y, button=button, clicks=clicks
            )
            return str(res)

        @self.mcp.tool(name="move_to")
        def move_to(x: float, y: float) -> str:
            """
            Move the mouse cursor to logical coordinates (x, y).
            x: logical coordinate from 0.0 (left) to 1.0 (right)
            y: logical coordinate from 0.0 (top) to 1.0 (bottom)
            """
            res = self.automation.execute_command("move_to", x=x, y=y)
            return str(res)

        @self.mcp.tool(name="drag_to")
        def drag_to(x: float, y: float, button: str = "left") -> str:
            """
            Drag the mouse from the current cursor position to logical coordinates (x, y).
            x: logical coordinate from 0.0 (left) to 1.0 (right)
            y: logical coordinate from 0.0 (top) to 1.0 (bottom)
            button: 'left', 'right', or 'middle'
            """
            res = self.automation.execute_command("drag_to", x=x, y=y, button=button)
            return str(res)

        @self.mcp.tool(name="scroll")
        def scroll(clicks: int) -> str:
            """
            Scroll the mouse wheel.
            clicks: number of scroll steps. Positive values scroll up, negative values scroll down.
            """
            res = self.automation.execute_command("scroll", clicks=clicks)
            return str(res)

        @self.mcp.tool(name="type")
        def type_text(text: str, mode: str = "auto") -> str:
            """
            Type or paste the specified text string on the keyboard.
            text: string to type or paste
            mode: 'auto' (automatic detection), 'keyboard' (keystroke emulation), or 'paste' (clipboard paste)
            """
            res = self.automation.execute_command("type", text=text, mode=mode)
            return str(res)

        @self.mcp.tool(name="press")
        def press_key(key: str) -> str:
            """
            Press a single key or key combination.
            key: key name (e.g. 'enter', 'tab', 'space', 'backspace', 'escape')
                 or key combination separated by plus/commas (e.g. 'ctrl+c', 'alt+tab')
            """
            # Handle key combinations: convert 'ctrl+c' to list ['ctrl', 'c']
            keys = [k.strip() for k in key.replace("+", ",").split(",")] if "+" in key or "," in key else key
            res = self.automation.execute_command("press", key=keys)
            return str(res)

        @self.mcp.tool(name="key_down")
        def key_down(key: str) -> str:
            """
            Hold down a keyboard key. Call key_up to release it.
            key: key name to press
            """
            res = self.automation.execute_command("key_down", key=key)
            return str(res)

        @self.mcp.tool(name="key_up")
        def key_up(key: str) -> str:
            """
            Release a held keyboard key.
            key: key name to release
            """
            res = self.automation.execute_command("key_up", key=key)
            return str(res)

        @self.mcp.tool(name="get_config")
        def get_config(key_path: str = "") -> str:
            """
            Get a configuration value using dot notation (e.g., 'display.width').
            If key_path is empty, returns the entire configuration object.
            """
            if not key_path:
                return str(self.config.config)
            val = self.config.get(key_path)
            return f"{key_path} = {val}"

        @self.mcp.tool(name="set_config")
        def set_config(key_path: str, value: str) -> str:
            """
            Set a configuration value using dot notation (e.g., 'display.width').
            Will attempt to parse the value as JSON (e.g., numbers, booleans) or use string.
            """
            try:
                import json
                parsed_val = json.loads(value)
            except Exception:
                parsed_val = value
            self.config.set(key_path, parsed_val)
            return f"Updated {key_path} to {parsed_val}"

    def _register_resources(self):
        """Registers MCP resources for the AI agent."""
        
        # FastMCP resource definition
        @self.mcp.resource("screen://current")
        def get_current_screen() -> bytes:
            """
            The current live screen capture of the virtual monitor.
            Returns binary PNG data.
            """
            try:
                return self.visual_state.get_screen_bytes(format_type="png", force=True)
            except Exception as e:
                logging.error(f"Error fetching current screen resource: {e}")
                return b""

    def run(self):
        """Runs the MCP server in either stdio or sse transport mode based on configuration."""
        transport = self.config.get("mcp.transport", "stdio")
        if transport == "sse":
            host = self.config.get("mcp.host", "0.0.0.0")
            port = int(self.config.get("mcp.port", 8001))
            
            # Configure FastMCP instance settings
            self.mcp.settings.host = host
            self.mcp.settings.port = port
            if hasattr(self.mcp.settings, "transport_security") and self.mcp.settings.transport_security:
                self.mcp.settings.transport_security.enable_dns_rebinding_protection = False
                self.mcp.settings.transport_security.allowed_hosts = ["*"]
                self.mcp.settings.transport_security.allowed_origins = ["*"]
            
            # Monkey patch sse_app to:
            # 1. Add Starlette CORSMiddleware
            # 2. Support POST and DELETE methods directly on the /sse endpoint (fixes 405 Method Not Allowed)
            original_sse_app = self.mcp.sse_app
            def patched_sse_app(*args, **kwargs):
                app = original_sse_app(*args, **kwargs)
                
                from starlette.responses import Response
                class NullResponse(Response):
                    async def __call__(self, scope, receive, send):
                        pass
                
                # Locate handle_sse / sse_endpoint and sse transport reference inside the app
                from starlette.routing import Route, Mount
                for i, route in enumerate(app.routes):
                    if isinstance(route, Route) and route.path == "/sse":
                        original_endpoint = route.endpoint
                        
                        # Find the post_message_app mounted on '/messages' (might be '/messages/')
                        post_message_app = None
                        for r in app.routes:
                            if isinstance(r, Mount) and r.path.startswith("/messages"):
                                post_message_app = r.app
                                break
                        
                        if post_message_app:
                            async def wrapped_endpoint(request):
                                if request.method == "POST":
                                    # Forward to post_message_app
                                    await post_message_app(request.scope, request.receive, request._send)
                                    return NullResponse()
                                elif request.method == "DELETE":
                                    session_id_param = request.query_params.get("session_id")
                                    if session_id_param:
                                        try:
                                            from uuid import UUID
                                            session_id = UUID(hex=session_id_param)
                                            # Get the bound transport class instance to clear writers
                                            sse_transport = getattr(post_message_app, "__self__", None)
                                            if sse_transport and hasattr(sse_transport, "_read_stream_writers"):
                                                writer = sse_transport._read_stream_writers.get(session_id)
                                                if writer:
                                                    await writer.aclose()
                                                    sse_transport._read_stream_writers.pop(session_id, None)
                                                    logging.info(f"Cleaned up SSE session {session_id} via DELETE request")
                                        except Exception as e:
                                            logging.error(f"Error handling DELETE for session {session_id_param}: {e}")
                                    return Response("Accepted", status_code=202)
                                return await original_endpoint(request)
                            
                            # Replace route with updated methods and wrapped endpoint
                            app.routes[i] = Route(
                                "/sse",
                                endpoint=wrapped_endpoint,
                                methods=["GET", "POST", "DELETE", "OPTIONS"]
                            )
                
                from starlette.middleware.cors import CORSMiddleware
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
                return app
            self.mcp.sse_app = patched_sse_app
                
            logging.info(f"Starting MCP Server (SSE transport) on http://{host}:{port} ...")
            self.mcp.run(transport="sse")
        else:
            logging.info("Starting MCP Server (stdio transport)...")
            self.mcp.run(transport="stdio")

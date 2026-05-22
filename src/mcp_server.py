# Implements: design/mcp_server.md
"""
MCP Server for the Virtual Monitor.
Interfaces with the official Python mcp SDK using FastMCP.
Exposes GUI automation tools and screen resources to AI agents.
"""

import sys
import logging
from mcp.server.fastmcp import FastMCP

# Global registry to track all instantiated SseServerTransport objects.
# This bypasses Starlette's routing/middleware boundaries when resolving active session writers.
active_transports = []
try:
    from mcp.server.sse import SseServerTransport
    from contextlib import asynccontextmanager

    # 1. Patch __init__ to track transports
    original_sse_init = SseServerTransport.__init__
    def patched_sse_init(self, *args, **kwargs):
        original_sse_init(self, *args, **kwargs)
        active_transports.append(self)
        logging.info(f"[MCP SSE] Tracked new SseServerTransport instance: {self}")
    SseServerTransport.__init__ = patched_sse_init

    # 2. Patch connect_sse to clean up dead sessions from _read_stream_writers on exit
    original_connect_sse = SseServerTransport.connect_sse
    @asynccontextmanager
    async def patched_connect_sse(self, scope, receive, send):
        pre_keys = set(self._read_stream_writers.keys())
        session_id = None
        try:
            async with original_connect_sse(self, scope, receive, send) as streams:
                post_keys = set(self._read_stream_writers.keys())
                new_keys = post_keys - pre_keys
                if new_keys:
                    session_id = list(new_keys)[0]
                    logging.info(f"[MCP SSE Patch] Intercepted new session: {session_id.hex}")
                yield streams
        finally:
            if session_id:
                self._read_stream_writers.pop(session_id, None)
                logging.info(f"[MCP SSE Patch] Cleaned up session: {session_id.hex}")
    SseServerTransport.connect_sse = patched_connect_sse

    # 3. Patch handle_post_message to intercept OPTIONS preflights
    original_handle_post = SseServerTransport.handle_post_message
    async def patched_handle_post(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("method") == "OPTIONS":
            from starlette.responses import Response
            response = Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, GET, OPTIONS, DELETE",
                    "Access-Control-Allow-Headers": "*",
                }
            )
            await response(scope, receive, send)
            return
        await original_handle_post(self, scope, receive, send)
    SseServerTransport.handle_post_message = patched_handle_post

    logging.info("[MCP SSE] Successfully applied all SseServerTransport monkey patches")
except Exception as e:
    logging.error(f"[MCP SSE] Failed to patch SseServerTransport: {e}")

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
            # 3. Handle session_id-less POST/DELETE gracefully via global transports list fallback
            # 4. Integrate RequestLoggingMiddleware for transparent debugging
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
                                # Helper to locate the active session writer from globally tracked SseServerTransport objects
                                def get_active_session():
                                    for t in reversed(active_transports):
                                        if hasattr(t, "_read_stream_writers") and t._read_stream_writers:
                                            writers = t._read_stream_writers
                                            if writers:
                                                session_id = list(writers.keys())[-1]
                                                return t, session_id, writers.get(session_id)
                                    return None, None, None

                                if request.method == "POST":
                                    session_id_param = request.query_params.get("session_id")
                                    if not session_id_param:
                                        # Auto-resolve and inject active session_id if missing
                                        _, target_session_id, _ = get_active_session()
                                        if target_session_id:
                                            request.scope["query_string"] = f"session_id={target_session_id.hex}".encode('utf-8')
                                            logging.info(f"[MCP SSE App] Auto-mapped session_id-less POST to session {target_session_id.hex}")
                                        else:
                                            logging.warning("[MCP SSE App] Received POST request without session_id and no active SSE session exists.")
                                            # Return friendly 400 Bad Request instructing the user/client to restart
                                            return Response(
                                                "Bad Request: No active SSE session found. Please establish a GET /sse connection first, or restart your client agent to refresh the session.",
                                                status_code=400,
                                                media_type="text/plain"
                                            )
                                    # Forward to post_message_app
                                    await post_message_app(request.scope, request.receive, request._send)
                                    return NullResponse()
                                elif request.method == "DELETE":
                                    session_id_param = request.query_params.get("session_id")
                                    transport, target_session_id, writer = get_active_session()
                                    if not session_id_param and target_session_id:
                                        session_id_param = target_session_id.hex
                                    if session_id_param:
                                        try:
                                            from uuid import UUID
                                            session_id = UUID(hex=session_id_param)
                                            # Find matching writer manually across transports if needed
                                            if not writer:
                                                for t in active_transports:
                                                    if hasattr(t, "_read_stream_writers") and session_id in t._read_stream_writers:
                                                        transport = t
                                                        writer = t._read_stream_writers[session_id]
                                                        break
                                            if writer and transport:
                                                await writer.aclose()
                                                transport._read_stream_writers.pop(session_id, None)
                                                logging.info(f"[MCP SSE App] Cleaned up SSE session {session_id} via DELETE request")
                                        except Exception as e:
                                            logging.error(f"[MCP SSE App] Error handling DELETE for session {session_id_param}: {e}")
                                    return Response("Accepted", status_code=202)
                                return await original_endpoint(request)
                            
                            # Replace route with updated methods and wrapped endpoint
                            app.routes[i] = Route(
                                "/sse",
                                endpoint=wrapped_endpoint,
                                methods=["GET", "POST", "DELETE", "OPTIONS"]
                            )
                from starlette.responses import JSONResponse
                from starlette.routing import Route

                # Add dummy endpoints for oauth protection discovery
                async def oauth_dummy_endpoint(request):
                    logging.info(f"[MCP SSE OAuth Dummy] Responding 200 OK to {request.method} {request.url.path}")
                    return JSONResponse(
                        {},
                        headers={
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, OPTIONS",
                            "Access-Control-Allow-Headers": "*",
                        }
                    )

                app.routes.append(Route("/.well-known/oauth-protected-resource", oauth_dummy_endpoint, methods=["GET", "OPTIONS"]))
                app.routes.append(Route("/.well-known/oauth-protected-resource/sse", oauth_dummy_endpoint, methods=["GET", "OPTIONS"]))

                from starlette.middleware.cors import CORSMiddleware
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
                
                # Add HTTP Request Logging Middleware for transparent connection state visibility
                class RequestLoggingMiddleware:
                    def __init__(self, app):
                        self.app = app
                    async def __call__(self, scope, receive, send):
                        if scope["type"] == "http":
                            method = scope.get("method", "UNKNOWN")
                            path = scope.get("path", "UNKNOWN")
                            query = scope.get("query_string", b"").decode("utf-8")
                            client = scope.get("client", None)
                            client_ip = client[0] if client else "unknown"
                            logging.info(f"[MCP SSE HTTP Log] Incoming request: {method} {path}?{query} from {client_ip}")
                            
                            async def log_send(message):
                                if message["type"] == "http.response.start":
                                    status = message.get("status", "unknown")
                                    logging.info(f"[MCP SSE HTTP Log] Responded: {method} {path} -> Status {status}")
                                await send(message)
                                
                            await self.app(scope, receive, log_send)
                        else:
                            await self.app(scope, receive, send)
                            
                app.add_middleware(RequestLoggingMiddleware)
                
                return app
            self.mcp.sse_app = patched_sse_app
                
            logging.info(f"Starting MCP Server (SSE transport) on http://{host}:{port} ...")
            self.mcp.run(transport="sse")
        else:
            logging.info("Starting MCP Server (stdio transport)...")
            self.mcp.run(transport="stdio")

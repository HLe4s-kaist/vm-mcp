# Implements: design/main.md
"""
Virtual Monitor MCP Server - Main Orchestrator.
Initializes the system, spins up Xvfb virtual frame buffer, sets up display environment variables,
and launches the Monitoring Bridge (asynchronously) and the MCP Server (blocking stdio).
"""

import os
import sys
import time
import logging
import subprocess
import asyncio
import threading
import atexit
import signal
import argparse

from config import ConfigurationManager


# Global reference to cleanup Xvfb
xvfb_process = None

def cleanup():
    """Cleans up the Xvfb virtual framebuffer process on exit."""
    global xvfb_process
    if xvfb_process:
        logging.info("Terminating Xvfb virtual display process...")
        try:
            xvfb_process.terminate()
            xvfb_process.wait(timeout=2)
            logging.info("Xvfb process terminated successfully.")
        except subprocess.TimeoutExpired:
            logging.warning("Xvfb did not terminate, killing it...")
            xvfb_process.kill()
            xvfb_process.wait()
            logging.info("Xvfb process killed.")
        except Exception as e:
            logging.error(f"Error during Xvfb cleanup: {e}")
        xvfb_process = None

def setup_xvfb(config):
    """Starts the Xvfb server based on configuration."""
    global xvfb_process
    display_num = config.get("display.display_num", 99)
    width = config.get("display.width", 1280)
    height = config.get("display.height", 800)
    color_depth = config.get("display.color_depth", 24)

    display_str = f":{display_num}"
    screen_resolution = f"{width}x{height}x{color_depth}"

    # Ensure ~/.Xauthority exists to avoid Xlib authentication errors
    xauth_path = os.path.expanduser("~/.Xauthority")
    if not os.path.exists(xauth_path):
        try:
            with open(xauth_path, "wb") as f:
                pass
            logging.info(f"Created empty Xauthority file at {xauth_path}")
        except Exception as e:
            logging.warning(f"Failed to create ~/.Xauthority: {e}")

    logging.info(f"Starting Xvfb on display {display_str} ({screen_resolution})...")
    
    # Check if a display server is already running on this display number
    # If so, we might want to kill it or use another one
    lock_file = f"/tmp/.X{display_num}-lock"
    if os.path.exists(lock_file):
        logging.warning(f"Lock file {lock_file} already exists. Cleaning up lock file.")
        try:
            os.remove(lock_file)
        except Exception as e:
            logging.error(f"Failed to remove lock file: {e}")

    try:
        # Run Xvfb command: Xvfb :99 -screen 0 1280x800x24
        xvfb_process = subprocess.Popen(
            ["Xvfb", display_str, "-screen", "0", screen_resolution],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Give Xvfb a moment to spin up
        time.sleep(1.5)
        
        # Check if process is still running
        if xvfb_process.poll() is not None:
            stdout, stderr = xvfb_process.communicate()
            raise RuntimeError(f"Xvfb failed to start. Return code: {xvfb_process.returncode}")
            
        logging.info(f"Xvfb started successfully. PID: {xvfb_process.pid}")
        
        # Set DISPLAY environment variable for this process and any child processes
        os.environ["DISPLAY"] = display_str
        logging.info(f"Set DISPLAY environment variable to {display_str}")
        
    except Exception as e:
        logging.error(f"Failed to start Xvfb: {e}")
        cleanup()
        sys.exit(1)

def signal_handler(signum, frame):
    """Handles standard shutdown signals."""
    logging.info(f"Received signal {signum}. Shutting down...")
    cleanup()
    sys.exit(0)

def main():
    # Configure logging to write strictly to stderr (important to avoid corrupting MCP stdin/stdout)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        stream=sys.stderr
    )

    # Parse CLI arguments to allow network exposure/transport override
    parser = argparse.ArgumentParser(description="Virtual Monitor MCP Server Orchestrator")
    parser.add_argument("--mcp-transport", choices=["stdio", "sse", "streamable-http"], help="MCP transport mode (stdio/sse/streamable-http)")
    parser.add_argument("--mcp-port", type=int, help="MCP SSE listener port (default: 8001)")
    parser.add_argument("--mcp-host", help="MCP SSE bind host (default: 0.0.0.0)")
    args = parser.parse_args()

    # Register exit handlers and signals
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.info("Initializing Virtual Monitor MCP Server System...")

    # 1. Load Configurations
    config_manager = ConfigurationManager()

    # Overwrite loaded config if CLI flags are explicitly passed
    if args.mcp_transport:
        config_manager.set("mcp.transport", args.mcp_transport)
    if args.mcp_port:
        config_manager.set("mcp.port", args.mcp_port)
    if args.mcp_host:
        config_manager.set("mcp.host", args.mcp_host)

    # 2. Setup Virtual Framebuffer (Xvfb)
    setup_xvfb(config_manager)

    # 3. Initialize Core Managers
    from visual_state import VisualStateManager
    from automation import AutomationWrapper
    from monitoring import MonitoringBridge
    from mcp_server import MCPServer

    visual_state = VisualStateManager(config_manager)
    automation = AutomationWrapper(config_manager, visual_state)

    # 4. Initialize Monitoring Bridge
    monitoring_bridge = MonitoringBridge(config_manager, visual_state, automation)

    # 5. Spin up the Monitoring Bridge Web Server in a background event loop/thread
    loop = asyncio.new_event_loop()
    
    def run_async_loop(loop):
        asyncio.set_event_loop(loop)
        # Start Web monitoring server
        loop.run_until_complete(monitoring_bridge.start())
        # Keep loop running forever
        loop.run_forever()

    threading.Thread(target=run_async_loop, args=(loop,), daemon=True).start()

    # Give the web server a second to start up
    time.sleep(1.0)

    # 6. Initialize and Run MCP Server (blocking stdio)
    mcp_server = MCPServer(config_manager, visual_state, automation)
    
    try:
        mcp_server.run()
    except Exception as e:
        logging.error(f"MCP Server crashed: {e}")
    finally:
        # Shutdown event loop
        loop.call_soon_threadsafe(loop.stop)
        cleanup()

if __name__ == "__main__":
    main()

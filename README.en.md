# Virtual Monitor MCP Server

[한국어 버전](README.md)

> [!IMPORTANT]
> This repository has all its code implemented by AI. All responsibilities lie with the user.

## Overview

This project aims to build a bridge that allows AI agents running in a CLI (Command Line Interface) environment to interact with and control GUI (Graphical User Interface) operating system environments in a manner similar to human users.

### Core Values
- **Headless Visualization**: Providing visual feedback by creating virtual monitors in headless server environments or virtual machines (VMs).
- **Agent-Centric Automation**: Providing interfaces for AI agents to view the screen, move the mouse, and type keyboard input to perform GUI-based tasks.
- **Real-Time Monitoring**: Providing a real-time observation web browser UI for users to monitor the agent's behavior.

## Core Features

1. **Virtual Monitor Creation**: Creates a virtual display (Xvfb) on headless systems to provide a GUI environment.
2. **GUI Interaction**: GUI automation features via PyAutoGUI:
    - Screen capture and reading
    - Mouse movement, clicks, and drags
    - Keyboard inputs (typing, hotkeys)
3. **MCP Protocol Support**: Allows AI agents to call tools using the Model Context Protocol (MCP).
4. **Web-based Monitoring**: Virtual desktop monitoring and remote control via a real-time web viewer (Port 8080).

## Installation & Usage Guide

### 1. Install System Packages
The following system packages are required for GUI automation and running the virtual framebuffer. (Based on Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y xvfb xdotool scrot python3-tk python3-dev
```

### 2. Install Python Dependencies
```bash
pip install pyautogui pillow websockets mcp mss starlette uvicorn pyperclip python-xlib asyncvnc numpy
```

### 3. Running the Project

#### Local stdio Mode (Default)
The AI agent (e.g., Claude Desktop) runs the process locally and communicates via stdin/stdout.
```bash
python3 src/main.py
```

#### Remote HTTP Mode (streamable-http)
Exposes an HTTP server for remote clients to connect over the network.
```bash
python3 src/main.py --mcp-transport streamable-http --mcp-port 8001
```

#### Existing VNC Server Integration (VNC Mode)
Connects to an existing VNC server (e.g., x11vnc, Windows VNC) to capture the screen and control it. It bypasses the creation of the Xvfb virtual framebuffer.
```bash
python3 src/main.py --automation-mode vnc --vnc-host 127.0.0.1 --vnc-port 5900 --vnc-password "your_password"
```
* **Shared VNC Connection**: Connects in `shared` mode by default, allowing you to monitor the same screen simultaneously alongside other VNC viewers.

Once running:
- Web Viewer: `http://localhost:8080` (Real-time monitoring and web-based control)
- MCP Endpoint: `http://localhost:8001/mcp/` (For AI agent integration)

### 4. Running Integration Tests

- **Port Binding & Web Page Load Test**:
  ```bash
  python3 tests/test_run.py
  ```
- **MCP stdio JSON-RPC Protocol Specification & Tool Call Test**:
  ```bash
  python3 tests/test_mcp.py
  ```
- **WebSocket-based Mouse/Keyboard Interaction Test**:
  ```bash
  python3 tests/test_interaction.py
  ```
- **Streamable HTTP Remote MCP Transport Test**:
  ```bash
  python3 tests/test_streamable_http.py
  ```

### 5. Running GUI Programs on the Virtual Display
The virtual display (Xvfb) starts with a blank (black) screen by default. To launch GUI programs for control:

#### 1) Install Test GUI Applications
```bash
sudo apt-get install -y x11-apps gedit
```

#### 2) Run Programs on the Virtual Display
```bash
# Run the xeyes demo where eyes track the cursor
./run_app.sh xeyes

# Run the text editor gedit
./run_app.sh gedit
```

## MCP Client Connection Guide

### Method 1: Local stdio Connection (Recommended)
Use this if running on a local machine, or if the AI agent spawns the process directly.

#### Claude Desktop Configuration Example
Add the following to your Claude Desktop config file (`claude_desktop_config.json`):

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "virtual-monitor": {
      "command": "python3",
      "args": ["/path/to/vmvm/src/main.py"]
    }
  }
}
```

### Method 2: Remote Streamable HTTP Connection
Use this to connect over the network to an MCP server running on a remote server (such as a VM).

#### 1) Server-side: Start in HTTP Mode
```bash
python3 src/main.py --mcp-transport streamable-http --mcp-port 8001 --mcp-host 0.0.0.0
```

#### 2) Client-side: Claude Desktop Configuration
```json
{
  "mcpServers": {
    "virtual-monitor": {
      "type": "streamable-http",
      "url": "http://<SERVER_IP>:8001/mcp/"
    }
  }
}
```
> Replace `<SERVER_IP>` with the actual IP address of the server.

#### 3) Programmatic Integration via Python Client
```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def main():
    url = "http://<SERVER_IP>:8001/mcp/"
    async with streamable_http_client(url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print([t.name for t in tools.tools])
            
            # Get screen metadata
            result = await session.call_tool("get_screen_metadata", {})
            print(result.content[0].text)
            
            # Take a screenshot
            screenshot = await session.call_tool("screenshot", {"format_type": "png"})
            print(f"Screenshot base64 length: {len(screenshot.content[0].text)}")

asyncio.run(main())
```

### Provided MCP Tools

| Tool Name | Description |
|-----------|-------------|
| `get_screen_metadata` | Retrieves screen resolution, display environment status, and metadata |
| `screenshot` | Takes a screenshot of the virtual monitor (returns Base64 string) |
| `click` | Clicks at logical coordinates (x, y normalized from 0.0 to 1.0) |
| `move_to` | Moves the mouse cursor |
| `drag_to` | Drags the mouse |
| `scroll` | Scrolls the mouse wheel |
| `type` | Types text (automatically chooses between keyboard typing and clipboard paste) |
| `press` | Presses a key or key combination (e.g. `ctrl+c`) |
| `key_down` | Holds down a key |
| `key_up` | Releases a held key |
| `get_config` | Retrieves system configuration |
| `set_config` | Updates system configuration |

### Provided MCP Resources

| Resource URI | Description |
|--------------|-------------|
| `screen://current` | Live screen capture of the virtual monitor (returns binary PNG data) |

### Network Troubleshooting

- **Firewall**: Make sure the port (default 8001) is not blocked by your firewall.
  ```bash
  sudo ufw allow 8001/tcp
  ```
- **Bind Host**: To allow external connections, make sure to specify `--mcp-host 0.0.0.0`.
- **Client Restart**: Remember to restart your client application (such as Claude Desktop) whenever the server restarts.

## License

This project is licensed under the GPLv2 (GNU General Public License v2.0). See the [LICENSE](LICENSE) file for details.

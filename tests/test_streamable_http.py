"""
Streamable HTTP transport integration test for MCP Server.
Tests the MCP server's streamable-http transport mode by:
1. Starting the server with --mcp-transport streamable-http
2. Connecting via the MCP SDK's streamable_http_client
3. Performing initialize handshake
4. Listing available tools
5. Calling the get_screen_metadata tool
6. Gracefully shutting down
"""

import subprocess
import sys
import time
import asyncio
import signal
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_streamable_http_mcp():
    """Test MCP server via streamable-http transport using the official MCP SDK client."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    server_host = "127.0.0.1"
    server_port = 8001
    server_url = f"http://{server_host}:{server_port}/mcp/"

    # Start the server process
    print("Starting MCP server with streamable-http transport...")
    proc = subprocess.Popen(
        [sys.executable, "src/main.py", "--mcp-transport", "streamable-http", "--mcp-port", str(server_port), "--mcp-host", server_host],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start up (Xvfb + uvicorn)
    print("Waiting for server to initialize...")
    time.sleep(5)

    # Check server is still running
    if proc.poll() is not None:
        stderr_output = proc.stderr.read()
        print(f"ERROR: Server exited prematurely. Stderr:\n{stderr_output}")
        sys.exit(1)

    errors = []
    try:
        print(f"Connecting to MCP server at {server_url}...")

        async with streamable_http_client(server_url) as (read_stream, write_stream, get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                # 1. Initialize
                print("Initializing MCP session...")
                result = await session.initialize()
                print(f"OK: Server initialized. Protocol version: {result.protocolVersion}")
                print(f"    Server: {result.serverInfo.name} v{result.serverInfo.version}")
                print(f"    Capabilities: {result.capabilities}")

                # 2. List tools
                print("\nListing available tools...")
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result.tools]
                print(f"OK: Found {len(tool_names)} tools: {tool_names}")

                # Verify expected tools exist
                expected_tools = ["get_screen_metadata", "screenshot", "click", "move_to", "drag_to", "scroll", "type", "press", "key_down", "key_up", "get_config", "set_config"]
                for tool_name in expected_tools:
                    if tool_name not in tool_names:
                        errors.append(f"Missing expected tool: {tool_name}")
                        print(f"ERROR: Missing expected tool: {tool_name}")

                # 3. Call get_screen_metadata tool
                print("\nCalling tool: get_screen_metadata...")
                tool_result = await session.call_tool("get_screen_metadata", {})
                print(f"OK: get_screen_metadata result: {tool_result.content[0].text[:200]}")

                # 4. Call get_config tool
                print("\nCalling tool: get_config...")
                config_result = await session.call_tool("get_config", {"key_path": "display.width"})
                print(f"OK: get_config result: {config_result.content[0].text}")

                # 5. List resources
                print("\nListing resources...")
                resources_result = await session.list_resources()
                resource_uris = [r.uri for r in resources_result.resources]
                print(f"OK: Found {len(resource_uris)} resources: {resource_uris}")

                session_id = get_session_id()
                print(f"\nSession ID: {session_id}")

        print("\n" + "="*60)
        if errors:
            print(f"FAILED: {len(errors)} error(s) found:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print("ALL TESTS PASSED: Streamable HTTP MCP transport works correctly!")

    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        print("\nTerminating server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
            print("Server terminated successfully.")
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            print("Server killed.")


if __name__ == "__main__":
    asyncio.run(test_streamable_http_mcp())

import subprocess
import json
import time
import sys

def test_mcp_protocol():
    print("Testing MCP Protocol via stdio...")
    
    # Start the server subprocess.
    # We must pipe stdin and stdout. stderr is captured to watch logs.
    proc = subprocess.Popen(
        [sys.executable, "src/main.py", "--mcp-transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for Xvfb and server initialization
    time.sleep(3)
    
    # 1. Send MCP Initialize Request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    
    try:
        # Write initialization request to stdin
        print("Sending initialize request...")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # Read initialization response from stdout (MCP response)
        # Skip any non-JSON or warning lines (like Xlib.xauth warning)
        response_data = None
        while True:
            stdout_line = proc.stdout.readline()
            if not stdout_line:
                break
            stripped = stdout_line.strip()
            print(f"Received line: {stripped}")
            if stripped.startswith("{"):
                try:
                    response_data = json.loads(stripped)
                    break
                except json.JSONDecodeError:
                    pass
                    
        if not response_data or "result" not in response_data:
            print(f"ERROR: Initialization failed. Expected result, got: {response_data}")
            sys.exit(1)
        print("OK: MCP Server initialized successfully.")
        
        # 2. Call tool: get_screen_metadata
        tool_call_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_screen_metadata",
                "arguments": {}
            }
        }
        
        print("Calling tool: get_screen_metadata...")
        proc.stdin.write(json.dumps(tool_call_request) + "\n")
        proc.stdin.flush()
        
        tool_response = None
        while True:
            tool_response_line = proc.stdout.readline()
            if not tool_response_line:
                break
            stripped = tool_response_line.strip()
            print(f"Received line: {stripped}")
            if stripped.startswith("{"):
                try:
                    tool_response = json.loads(stripped)
                    break
                except json.JSONDecodeError:
                    pass
                    
        if not tool_response or "result" not in tool_response:
            print(f"ERROR: Tool call failed: {tool_response}")
            sys.exit(1)
            
        print("OK: Tool call get_screen_metadata completed successfully.")
        
    except Exception as e:
        print(f"ERROR during test: {e}")
        # Print stderr log for debugging
        sys.exit(1)
        
    finally:
        print("Terminating server...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
            print("Server terminated successfully.")
        except Exception:
            proc.kill()
            proc.wait()
            print("Server killed.")

if __name__ == "__main__":
    test_mcp_protocol()

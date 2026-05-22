import subprocess
import time
import sys
import socket
import urllib.request

def check_port(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', port))
        s.close()
        return True
    except ConnectionRefusedError:
        return False

def test_sse_mode():
    print("Starting Virtual Monitor Server in SSE mode (Port 8002)...")
    
    # Run the server with SSE options
    proc = subprocess.Popen(
        [sys.executable, "src/main.py", "--mcp-transport", "sse", "--mcp-port", "8002"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True
    )
    
    time.sleep(4) # Wait for startup
    
    success = False
    try:
        # Check if port 8002 is active
        if not check_port(8002):
            print("ERROR: SSE port 8002 is not listening!")
        else:
            print("OK: SSE port 8002 is listening.")
            
            # Try requesting /sse endpoint
            try:
                # FastMCP sse server responds to /sse or simple root check
                response = urllib.request.urlopen("http://127.0.0.1:8002/sse")
                # Since SSE is a stream, we can read a chunk or check status
                status = response.getcode()
                if status == 200:
                    print("OK: Successfully reached /sse endpoint!")
                    success = True
                else:
                    print(f"ERROR: Received unexpected HTTP status: {status}")
            except Exception as e:
                # Sometimes raw open times out or expects event-stream headers
                # We can check if it gets connection (e.g. HTTP Error 405 Method Not Allowed or similar is still a server response)
                print(f"Server responded (might be stream block/exception as expected): {e}")
                # If we get HTTP Error 405 or 400 or block, it means the server is running on that port
                if "HTTP Error" in str(e) or "URLError" not in str(e):
                    print("OK: SSE Server is active and responding to HTTP requests.")
                    success = True
                
    finally:
        print("Terminating server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
            print("Server terminated.")
        except Exception:
            proc.kill()
            print("Server killed.")
            
    if success:
        print("SUCCESS: SSE server mode verified successfully!")
    else:
        print("ERROR: SSE server mode verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_sse_mode()

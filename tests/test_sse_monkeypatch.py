import subprocess
import time
import sys
import socket
import urllib.request
import urllib.error
import json

def check_port(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', port))
        s.close()
        return True
    except ConnectionRefusedError:
        return False

def test_sse_monkeypatch():
    port = 8003
    print(f"Starting Virtual Monitor Server in SSE mode for Monkeypatch testing (Port {port})...")
    
    # Run the server
    proc = subprocess.Popen(
        [sys.executable, "src/main.py", "--mcp-transport", "sse", "--mcp-port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True
    )
    
    time.sleep(5) # Wait for startup
    
    success = False
    try:
        if not check_port(port):
            print(f"ERROR: Port {port} is not listening!")
            return False
            
        print(f"OK: Port {port} is listening. Testing CORS/OPTIONS on /sse...")
        
        # 1. Test OPTIONS /sse (Preflight)
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/sse",
            method="OPTIONS"
        )
        req.add_header("Origin", "http://example.com")
        req.add_header("Access-Control-Request-Method", "POST")
        try:
            with urllib.request.urlopen(req) as response:
                print(f"OPTIONS Response code: {response.getcode()}")
                headers = dict(response.info())
                print(f"OPTIONS Headers: {headers}")
                assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers
                print("OK: CORS Preflight allowed.")
        except Exception as e:
            print(f"ERROR on OPTIONS: {e}")
            return False
            
        # 2. Test POST /sse with invalid session_id (should NOT be 405 Method Not Allowed)
        # Expected: 400 or 404 (because session_id does not exist or is invalid)
        req_post = urllib.request.Request(
            f"http://127.0.0.1:{port}/sse?session_id=00000000000000000000000000000000",
            data=b'{"jsonrpc":"2.0","method":"ping","id":1}',
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req_post) as resp:
                print(f"Unexpected POST success: {resp.getcode()}")
        except urllib.error.HTTPError as e:
            print(f"POST Response code (Expected 404/400): {e.code}")
            # If 405 occurs, the monkeypatch failed!
            if e.code == 405:
                print("ERROR: POST /sse still returned 405 Method Not Allowed!")
                return False
            elif e.code in (400, 404):
                print("OK: POST /sse routed correctly (not 405).")
            else:
                print(f"WARNING: Unexpected HTTPError code {e.code}")
        except Exception as e:
            print(f"Unexpected POST exception: {e}")
            return False
            
        # 3. Test DELETE /sse (should return 202 Accepted even if session_id is random/invalid)
        req_delete = urllib.request.Request(
            f"http://127.0.0.1:{port}/sse?session_id=00000000000000000000000000000000",
            method="DELETE"
        )
        try:
            with urllib.request.urlopen(req_delete) as resp:
                print(f"DELETE Response code: {resp.getcode()}")
                if resp.getcode() == 202:
                    print("OK: DELETE /sse routed correctly and returned 202.")
                else:
                    print(f"ERROR: DELETE /sse returned unexpected status {resp.getcode()}")
                    return False
        except urllib.error.HTTPError as e:
            print(f"ERROR: DELETE /sse failed with HTTPError: {e.code} ({e.reason})")
            if e.code == 405:
                print("ERROR: DELETE /sse returned 405 Method Not Allowed!")
            return False
        except Exception as e:
            print(f"DELETE Exception: {e}")
            return False

        # 4. Test POST /sse without session_id (No active sessions) -> Should return 400 Bad Request
        req_post_no_session = urllib.request.Request(
            f"http://127.0.0.1:{port}/sse",
            data=b'{"jsonrpc":"2.0","method":"ping","id":1}',
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req_post_no_session) as resp:
                print(f"Unexpected POST success without session: {resp.getcode()}")
                return False
        except urllib.error.HTTPError as e:
            print(f"POST without session response code (Expected 400): {e.code}")
            if e.code != 400:
                print(f"ERROR: Expected 400 Bad Request, got {e.code}")
                return False
            print("OK: POST /sse without session_id returned 400 Bad Request as expected.")
        except Exception as e:
            print(f"Unexpected POST without session exception: {e}")
            return False

        # 5. Test POST /sse without session_id (With active session) -> Should return 202 Accepted due to auto-mapping fallback
        print("Establishing dummy SSE connection to trigger session creation...")
        try:
            # We use urllib to open a stream connection and keep it open (do not read the whole thing at once)
            sse_conn = urllib.request.urlopen(f"http://127.0.0.1:{port}/sse", timeout=5)
            # Give a tiny slice of time for server to store session
            time.sleep(0.5)
            
            # Send POST without session_id
            req_post_auto_map = urllib.request.Request(
                f"http://127.0.0.1:{port}/sse",
                data=b'{"jsonrpc":"2.0","method":"ping","id":1}',
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req_post_auto_map) as resp:
                print(f"Auto-mapped POST Response code: {resp.getcode()}")
                if resp.getcode() == 202:
                    print("OK: POST /sse without session_id was successfully auto-mapped to active session and returned 202 Accepted.")
                    success = True
                else:
                    print(f"ERROR: Auto-mapped POST returned unexpected code {resp.getcode()}")
                    return False
            
            # Clean up the GET connection
            sse_conn.close()
        except Exception as e:
            print(f"ERROR during active session auto-mapping test: {e}")
            return False

    finally:
        print("Terminating server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
            print("Server terminated.")
        except Exception:
            proc.kill()
            print("Server killed.")
            
    return success

if __name__ == "__main__":
    if test_sse_monkeypatch():
        print("SUCCESS: SSE Monkeypatch test verified!")
        sys.exit(0)
    else:
        print("ERROR: SSE Monkeypatch test failed!")
        sys.exit(1)

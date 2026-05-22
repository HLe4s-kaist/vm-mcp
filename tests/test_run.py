import subprocess
import time
import socket
import urllib.request
import sys
import os

def check_port(port):
    """Checks if a port is open."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', port))
        s.close()
        return True
    except ConnectionRefusedError:
        return False

def test_server():
    print("Starting Virtual Monitor Server in test mode...")
    
    # Run the main.py server as a background subprocess
    # Redirect stdout and stderr to a file so we can debug if it fails
    log_file = open("test_server_run.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE, # Keep stdin open for MCP stdio protocol
        text=True
    )
    
    time.sleep(3) # Wait for Xvfb and web server to spin up
    
    try:
        # Check if port 8080 is listening
        if not check_port(8080):
            print("ERROR: Monitoring port 8080 is not listening!")
            # Get any stderr
            proc.terminate()
            stdout, stderr = proc.communicate(timeout=2)
            print("Server stdout:\n", stdout)
            print("Server stderr:\n", stderr)
            sys.exit(1)
            
        print("OK: Port 8080 is listening.")
        
        # Try fetching the index HTML page
        try:
            response = urllib.request.urlopen("http://127.0.0.1:8080/")
            html = response.read().decode('utf-8')
            if "VM Monitor Bridge" in html:
                print("OK: Monitoring web page successfully served and verified!")
            else:
                print("ERROR: Served HTML did not contain 'VM Monitor Bridge'!")
                sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to connect to http://127.0.0.1:8080/ : {e}")
            sys.exit(1)
            
    finally:
        print("Terminating test server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
            print("Test server terminated successfully.")
        except Exception:
            proc.kill()
            proc.wait()
            print("Test server killed.")
            
if __name__ == "__main__":
    test_server()

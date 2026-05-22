import subprocess
import time
import sys
import json
import asyncio
import websockets

async def send_websocket_events():
    uri = "ws://127.0.0.1:8080/ws"
    print(f"Connecting to WebSocket at {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected. Sending interactive events...")
            
            # 1. Send mouse_down
            mouse_down_event = {
                "type": "mouse_down",
                "x": 0.5,
                "y": 0.5,
                "button": "left"
            }
            await websocket.send(json.dumps(mouse_down_event))
            print("Sent mouse_down event.")
            await asyncio.sleep(0.5)
            
            # 2. Send mouse_move
            mouse_move_event = {
                "type": "mouse_move",
                "x": 0.6,
                "y": 0.6
            }
            await websocket.send(json.dumps(mouse_move_event))
            print("Sent mouse_move event.")
            await asyncio.sleep(0.5)
            
            # 3. Send mouse_up
            mouse_up_event = {
                "type": "mouse_up",
                "x": 0.6,
                "y": 0.6,
                "button": "left"
            }
            await websocket.send(json.dumps(mouse_up_event))
            print("Sent mouse_up event.")
            await asyncio.sleep(0.5)
            
            # 4. Send scroll
            scroll_event = {
                "type": "scroll",
                "clicks": -100
            }
            await websocket.send(json.dumps(scroll_event))
            print("Sent scroll event.")
            await asyncio.sleep(0.5)
            
            # 5. Send custom text typing fallback test
            type_event = {
                "type": "type",
                "text": "Hello, Antigravity!"
            }
            await websocket.send(json.dumps(type_event))
            print("Sent text type event.")
            await asyncio.sleep(0.5)
            
            print("All interactive events sent successfully!")
            return True
    except Exception as e:
        print(f"WebSocket client error: {e}")
        return False

def test_interaction():
    print("Starting Virtual Monitor Server in interaction test mode...")
    
    # Run the main.py server as a background subprocess
    proc = subprocess.Popen(
        [sys.executable, "src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True
    )
    
    time.sleep(4) # Wait for Xvfb and web server to spin up
    
    success = False
    try:
        # Run async websocket sender
        success = asyncio.run(send_websocket_events())
    except Exception as e:
        print(f"Error during interaction test: {e}")
    finally:
        print("Terminating test server...")
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=3)
            print("Server stdout lines:", len(stdout.splitlines()))
            print("Server stderr lines:", len(stderr.splitlines()))
            if not success:
                print("Server stderr output:")
                print(stderr)
        except Exception:
            proc.kill()
            proc.wait()
            print("Test server killed.")
            
    if not success:
        print("ERROR: Interaction test failed.")
        sys.exit(1)
    else:
        print("SUCCESS: Interaction test completed without errors!")

if __name__ == "__main__":
    test_interaction()

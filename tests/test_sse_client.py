import asyncio
import httpx
from httpx_sse import aconnect_sse
import sys
import json
import urllib.parse

async def run_client(server_url):
    print(f"Connecting to SSE server at {server_url} ...")
    
    endpoint_received = asyncio.Event()
    absolute_endpoint = None
    success = False
    
    async def listen_and_act(event_source):
        nonlocal absolute_endpoint, success
        try:
            async for event in event_source.aiter_sse():
                if event.event == "endpoint":
                    endpoint_url = event.data
                    print(f"Received message endpoint: {endpoint_url}")
                    absolute_endpoint = urllib.parse.urljoin(server_url, endpoint_url)
                    print(f"Resolved endpoint: {absolute_endpoint}")
                    endpoint_received.set()
                elif event.event == "message":
                    msg = json.loads(event.data)
                    print(f"[SSE Message Received]:\n{json.dumps(msg, indent=2)}")
                    # Check if we got the response for our get_screen_metadata call (id: 2)
                    if msg.get("id") == 2:
                        success = True
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"SSE stream listener encountered error: {e}")

    async with httpx.AsyncClient() as client:
        try:
            async with aconnect_sse(client, "GET", server_url) as event_source:
                print("SSE Connection established.")
                
                # Start listener task
                listener_task = asyncio.create_task(listen_and_act(event_source))
                
                # Wait for endpoint event
                try:
                    await asyncio.wait_for(endpoint_received.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    print("Error: Timeout waiting for endpoint event from SSE server.")
                    listener_task.cancel()
                    return False
                
                # 2. Send 'initialize' request
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "python-test-client", "version": "1.0"}
                    }
                }
                
                print(f"Sending 'initialize' request to {absolute_endpoint}...")
                resp = await client.post(absolute_endpoint, json=init_payload)
                print(f"POST (initialize) Response Status: {resp.status_code}")
                if resp.status_code not in (200, 202):
                    print(f"Error sending initialize: {resp.text}")
                    listener_task.cancel()
                    return False
                
                await asyncio.sleep(1.0) # Wait for response on SSE stream
                
                # 3. Call tool 'get_screen_metadata'
                tool_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "get_screen_metadata",
                        "arguments": {}
                    }
                }
                print(f"Calling tool 'get_screen_metadata'...")
                resp = await client.post(absolute_endpoint, json=tool_payload)
                print(f"POST (tools/call) Response Status: {resp.status_code}")
                
                await asyncio.sleep(1.5) # Wait for response on SSE stream
                
                # 4. Clean up: Cancel listener and send DELETE
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass
                
                # Send DELETE request to close session
                print("Sending DELETE request to close session...")
                delete_resp = await client.delete(server_url)
                print(f"DELETE Response Status: {delete_resp.status_code}")
                
                return success
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001/sse"
    success = asyncio.run(run_client(url))
    if success:
        print("\nSSE Client interaction test PASSED!")
        sys.exit(0)
    else:
        print("\nSSE Client interaction test FAILED!")
        sys.exit(1)

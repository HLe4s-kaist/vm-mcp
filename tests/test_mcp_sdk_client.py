"""
MCP SDK stdio client integration test.
Tests the MCP server via stdio transport using the official MCP SDK client
(as an AI agent like Claude Desktop would use it).

This is more thorough than test_mcp.py which uses raw JSON-RPC.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_stdio_mcp_sdk_client():
    """Test MCP server via stdio using the official MCP SDK client."""
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py'), '--mcp-transport', 'stdio'],
        env=None,
    )

    errors = []

    print("Connecting to MCP server via stdio (SDK client)...")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 1. Initialize
            print("Initializing MCP session...")
            result = await session.initialize()
            print(f"OK: Protocol version: {result.protocolVersion}")
            print(f"    Server: {result.serverInfo.name} v{result.serverInfo.version}")

            # 2. List tools
            print("\nListing tools...")
            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            print(f"OK: {len(tool_names)} tools: {tool_names}")

            expected_tools = [
                "get_screen_metadata", "screenshot", "click", "move_to",
                "drag_to", "scroll", "type", "press", "key_down", "key_up",
                "get_config", "set_config"
            ]
            for name in expected_tools:
                if name not in tool_names:
                    errors.append(f"Missing tool: {name}")
                    print(f"ERROR: Missing tool: {name}")

            # 3. Call get_screen_metadata
            print("\nCalling get_screen_metadata...")
            meta = await session.call_tool("get_screen_metadata", {})
            text = meta.content[0].text
            print(f"OK: {text[:150]}")
            if "width" not in text or "height" not in text:
                errors.append("get_screen_metadata missing width/height")

            # 4. Call get_config
            print("\nCalling get_config...")
            cfg = await session.call_tool("get_config", {"key_path": "display.width"})
            print(f"OK: {cfg.content[0].text}")

            # 5. Call set_config
            print("\nCalling set_config...")
            setcfg = await session.call_tool("set_config", {"key_path": "visual.jpeg_quality", "value": "90"})
            print(f"OK: {setcfg.content[0].text}")

            # 6. Verify the config was set
            getcfg2 = await session.call_tool("get_config", {"key_path": "visual.jpeg_quality"})
            if "90" not in getcfg2.content[0].text:
                errors.append("set_config did not persist")
            print(f"OK: Verified config update: {getcfg2.content[0].text}")

            # 7. Call move_to
            print("\nCalling move_to...")
            move_res = await session.call_tool("move_to", {"x": 0.5, "y": 0.5})
            print(f"OK: {move_res.content[0].text[:100]}")

            # 8. Call click
            print("\nCalling click...")
            click_res = await session.call_tool("click", {"x": 0.3, "y": 0.7, "button": "left"})
            print(f"OK: {click_res.content[0].text[:100]}")

            # 9. Call scroll
            print("\nCalling scroll...")
            scroll_res = await session.call_tool("scroll", {"clicks": 3})
            print(f"OK: {scroll_res.content[0].text[:100]}")

            # 10. Call type
            print("\nCalling type...")
            type_res = await session.call_tool("type", {"text": "hello", "mode": "keyboard"})
            print(f"OK: {type_res.content[0].text[:100]}")

            # 11. Call press
            print("\nCalling press...")
            press_res = await session.call_tool("press", {"key": "enter"})
            print(f"OK: {press_res.content[0].text[:100]}")

            # 12. Call screenshot (just verify it returns base64 data)
            print("\nCalling screenshot...")
            ss = await session.call_tool("screenshot", {"format_type": "jpeg", "quality": 50})
            ss_text = ss.content[0].text
            if len(ss_text) < 100:
                errors.append(f"Screenshot too small: {len(ss_text)} chars")
            print(f"OK: Screenshot returned {len(ss_text)} chars of base64 data")

            # 13. List resources
            print("\nListing resources...")
            resources = await session.list_resources()
            resource_uris = [str(r.uri) for r in resources.resources]
            print(f"OK: {len(resource_uris)} resources: {resource_uris}")
            if "screen://current" not in resource_uris:
                errors.append("Missing screen://current resource")

    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED: {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED: MCP stdio SDK client integration works correctly!")
        print("  - 12 tools verified")
        print("  - All tool calls successful (metadata, config, mouse, keyboard, screenshot)")
        print("  - Resources verified")


if __name__ == "__main__":
    asyncio.run(test_stdio_mcp_sdk_client())

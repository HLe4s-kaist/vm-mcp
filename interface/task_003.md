# Task 3: Refactor MCP Interface to MCP Server

## Goal
Refactor the design documentation to reflect that the MCP interface is now considered a single "MCP Server" component rather than just "Tool Mapping", and reorganize the file structure.

## Steps
1. **Modify `design/main.md`**:
    - Change section `### 2.1 MCP Tool/Resource Provider (인터페이스 제공자)` to `### 2.1 MCP Server`.
    - Update the reference in section 2.1 to point to the new `design/mcp_server.md` and make it a general reference for the section.
    - Remove the specific reference from the "Tool Mapping" line.
2. **Refactor File Structure**:
    - Move `design/mcp_interface/tool_mapping.md` to `design/mcp_server.md`.
    - Delete the `design/mcp_interface/` directory.
3. **Update `MEMORY.md`**:
    - Update the design document references to reflect the new file paths.

## Verification
- Check `design/main.md` for correct title and references.
- Check `design/mcp_server.md` exists.
- Check `design/mcp_interface/` is removed.
- Check `MEMORY.md` is updated correctly.

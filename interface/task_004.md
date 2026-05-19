# Task 4: Redesign MCP Server detailed specification

## Goal
Rewrite `design/mcp_server.md` based on the high-level description in `design/main.md` section 2.1, ignoring the previous content of `design/mcp_server.md`.

## Steps
1. **Analyze requirements from `design/main.md` (Section 2.1)**:
    - **Tool Mapping**: Map agent tool names (e.g., `click`, `type`) to internal automation functions.
    - **Resource Exposure**: Provide current screenshots or system status as MCP resources.
    - **Request/Response Handler**: Validate RPC request parameters and return results in a format understandable by the agent.
2. **Draft the new detailed design for `design/mcp_server.md`**:
    - Define the architecture for the three core sub-modules:
        - `Tool Mapper`
        - `Resource Provider`
        - `RPC Handler`
    - For each sub-module, define:
        - Responsibility
        - Key responsibilities/functions
        - Data flow/Interaction
3. **Overwrite `design/mcp_server.md`** with the new content.
4. **Update `MEMORY.md`** (if necessary, but the file path is the same).

## Expected Output
A refined `design/mcp_server.md` that provides technical depth for the MCP Server component without unnecessary fluff.

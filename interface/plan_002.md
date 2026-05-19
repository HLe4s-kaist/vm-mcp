# Plan: Design Tool Mapping for MCP Interface Manager

## Objective
Design the "Tool Mapping" component within the MCP Interface Manager, as specified in `design/main.md`. This component will bridge the gap between MCP tool calls and the actual automation functions.

## Proposed Structure for `design/mcp_interface/tool_mapping.md`
The document will be written in Korean and include the following sections:

1.  **개요 (Overview)**:
    - Tool Mapping의 역할 및 목적.
    - MCP 프로토콜과 내부 자동화 함수 간의 연결 원리.
2.  **매핑 메커니즘 (Mapping Mechanism)**:
    - **명칭 매핑 (Name Mapping)**: MCP Tool Name $\leftrightarrow$ Internal Function Name.
    - **파라미터 매핑 (Parameter Mapping)**: MCP Argument $\leftrightarrow$ Function Argument (Type conversion, default values).
3.  **검증 및 처리 프로세스 (Validation & Processing)**:
    - **도구 존재 여부 검증 (Tool Existence Check)**.
    - **파라미터 유효성 검사 (Parameter Validation)**: 타입 체크, 범위 체크 등.
    - **오류 처리 (Error Handling)**: 잘못된 도구 호출이나 파라미터에 대한 MCP 에러 응답 설계.
4.  **확장성 설계 (Extensibility)**:
    - 새로운 도구가 추가될 때의 등록 방식 (예: Decorator, Registry pattern).

## Execution Steps
1.  Draft the design content in Korean.
2.  Save the file to `design/mcp_interface/tool_mapping.md`.
3.  Update `design/main.md` to include a link/reference to `design/mcp_interface/tool_mapping.md` in the corresponding section.
4.  Verify the file content and the update in `main.md`.

## Verification
- 파일이 `design/mcp_interface/` 디렉토리에 존재하는지 확인.
- `design/main.md`에 해당 파일에 대한 링크/참조가 추가되었는지 확인.
- 내용이 체계적이고 설계 중심인지 확인.
- 한국어로 작성되었는지 확인.
- MCP Tool 명세와 일치하는지 확인.

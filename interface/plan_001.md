# Plan: Create design/main.md

## Objective
Create a comprehensive, structured, and systematic overall design document (`design/main.md`) for the "Virtual Monitor MCP Server" project.

## Proposed Structure for design/main.md
The document will be written in Korean and include the following sections:

1.  **시스템 개요 (System Overview)**:
    - 프로젝트의 목적 및 핵심 가치.
    - 해결하고자 하는 문제 (CLI와 GUI 환경의 격차 해소).
2.  **시스템 아키텍처 (System Architecture)**:
    - 고수준 아키텍처 다이어그램 (텍스트 기반 설명).
    - 주요 계층 구조 (Client -> MCP Server -> Controller -> Virtual Monitor/Target System).
3.  **핵심 구성 요소 (Core Components)**:
    - **MCP 인터페이스 관리자 (MCP Interface Manager)**: 도구 및 리소스 정의 및 관리.
    - **GUI 컨트롤러 (GUI Controller)**: 마우스, 키보드, 스크린 캡처 제어 로직.
    - **모니터링 서비스 (Monitoring Service)**: VNC 및 웹 기반 시각화 인터페이스.
    - **가상 모니터 브릿지 (Virtual Monitor Bridge)**: 타겟 시스템(VMware, QEMU 등)과의 통신.
4.  **데이터 흐름 (Data Flow)**:
    - 에이전트의 명령이 실제 GUI 동작으로 변환되는 과정.
    - 스크린 데이터가 사용자/에이전트에게 전달되는 과정.
5.  **상세 설계 (Detailed Design)**:
    - **MCP 도구 명세 (MCP Tool Specifications)**: `click`, `type`, `screenshot` 등의 상세 동작 및 파라미터.
    - **통신 프로토콜 (Communication Protocols)**: MCP, VNC, HTTP/WebSocket.
6.  **기술 스택 (Technology Stack)**:
    - 언어, 프레임워크, 라이브러리 제안.
7.  **확장성 및 보안 (Scalability & Security)**:
    - 향후 확장 계획 및 보안 고려 사항.

## Execution Steps
1.  Draft the content in Korean based on the proposed structure.
2.  Ensure the content is strictly design-oriented, avoiding implementation details unless necessary for architectural understanding.
3.  Save the file to `design/main.md`.
4.  Verify the file content.

## Verification
- 파일이 `design/` 디렉토리에 존재하는지 확인.
- 내용이 체계적이고 구조적인지 확인.
- 한국어로 작성되었는지 확인.
- 설계에 관한 내용만 포함되어 있는지 확인.

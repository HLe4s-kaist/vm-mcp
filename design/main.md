# Virtual Monitor MCP Server: 시스템 설계 명세 (Main Design Specification)

## 1. 시스템 아키텍처 (System Architecture)

본 시스템은 기존의 검증된 자동화 도구(예: `pyautogui`, VNC 서버 등)를 MCP(Model Context Protocol) 인터페이스로 래핑(Wrapping)하여, AI 에이전트가 GUI 환경을 제어할 수 있도록 하는 **통합 인터페이스 서버**이다.

### 1.1 계층 구조 (Layered Architecture)

1.  **Protocol Layer (MCP Interface)**: 에이전트의 JSON-RPC 요청을 수신하고 응답하는 최상위 인터페이스 계층.
2.  **Integration Layer (Automation Wrapper)**: MCP 명령을 실제 자동화 라이브러리나 도구의 함수 호출로 변환하는 핵심 로직 계층.
3.  **Tool/Driver Layer (Existing Tools)**: 실제 GUI 조작 및 화면 캡처를 수행하는 외부 라이브러리 및 가상화 도구 계층.
4.  **Monitoring Layer (External Access)**: 에이전트 외에 사용자(인간)가 시스템을 관찰할 수 있도록 지원하는 부가 서비스 계층.

### 1.2 고수준 구성도 (High-Level Diagram)
```text
[ AI Agent ] <--- MCP Protocol ---> [ MCP Server ]
                                            |
                                [ Automation Wrapper ]
                                     /             \
                 [ Existing Tools ] <--- [ Visual Manager ] ---> [ Monitoring Bridge ]
                        |                                               |
                 [ Target System ]                              [ Web/VNC Client ]
```

---

## 2. 핵심 컴포넌트 설계 (Core Components Design)

각 컴포넌트는 기존 도구를 효율적으로 활용하고 MCP 표준에 맞게 노출하는 데 집중한다.

### 2.1 MCP Server
MCP 프로토콜 규격을 준수하며, 에이전트에게 기능을 노출하는 컴포넌트이다. (상세 설계: [design/mcp_server.md](./design/mcp_server.md))

- **Tool Mapping**: 에이전트가 호출하는 `click`, `type` 등의 도구 이름을 내부 자동화 함수와 매핑한다.

- **Resource Exposure**: 현재 스크린샷이나 시스템 상태를 MCP 리소스로 에이전트에게 제공한다.
- **Request/Response Handler**: RPC 요청의 파라미터를 검증하고, 실행 결과를 에이전트가 이해할 수 있는 형식으로 반환한다.

### 2.2 Automation Wrapper (자동화 래퍼)
기존 자동화 도구를 MCP 환경에 맞게 최적화하여 사용하는 핵심 로직 계층이다.
- **Library Integration**: `pyautogui`나 OS 레벨의 자동화 API를 호출하여 실제 동작을 수행한다.
- **Coordinate Transformer**: 에이전트가 사용하는 논리적 좌표를 실제 디스플레이 해상도 및 스크린 좌표계에 맞게 변환한다.
- **Execution Guard**: 명령 실행 중 발생할 수 있는 예외(예: 화면 해상도 변경, 권한 문제)를 처리하고 안정적인 실행을 보장한다.

### 2.3 Visual State Manager (비주얼 상태 관리자)
시각적 데이터를 캡처하고 관리하여 에이전트와 모니터링 서비스에 전달한다.
- **Capture Engine**: 기존 스크린샷 라이브러리나 가상 디스플레이 API를 사용하여 현재 화면 데이터를 추출한다.
- **Format Converter**: 추출된 데이터를 MCP 리소스용 이미지 데이터 또는 스트리밍용 인코딩 데이터로 변환한다.

### 2.4 Monitoring Bridge (모니터링 브릿지)
MCP 에이전트와 별개로, 사용자가 시스템을 관찰할 수 있는 채널을 제공한다.
- **Web/VNC Streamer**: `Visual State Manager`로부터 받은 데이터를 웹(WebSocket)이나 VNC 프로토콜로 중계한다.
- **External Interface**: 에이전트의 동작을 실시간으로 시각화하여 사용자에게 제공하는 인터페이스를 유지한다.

---

## 3. 컴포넌트 간 상호작용 (Component Interaction)

### 3.1 명령 실행 흐름 (Command Execution Flow)
`MCP Provider`가 명령 수신 $\rightarrow$ `Automation Wrapper`가 좌표 변환 및 라이브러리 호출 $\rightarrow$ `Existing Tools`가 실제 GUI 조작 수행 $\rightarrow$ 결과 반환.

### 3.2 시각 정보 제공 흐름 (Visual Observation Flow)
`Visual State Manager`가 화면 캡처 $\rightarrow$ (에이전트용) `MCP Provider`를 통해 리소스로 제공 **및** (사용자용) `Monitoring Bridge`를 통해 웹/VNC로 스트리밍.

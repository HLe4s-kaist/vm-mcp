# MCP Server 상세 설계 명세 (Detailed Design Specification)

## 1. 아키텍처 개요 (Architectural Overview)
MCP Server는 에이전트의 요청을 수신하여 실행 명령(Tools) 또는 데이터 요청(Resources)으로 분기 처리하고, 결과를 표준화된 프로토콜 형식으로 반환하는 유기적인 컴포넌트 집합이다.

## 2. 컴포넌트 상세 설계 (Component Detail Design)

### 2.1 통신 및 라우팅 계층 (Communication & Routing Layer)
가장 바깥쪽에서 프로토콜 규격을 유지하고 요청을 적절한 경로로 전달한다.
- **JSON-RPC Interface**: MCP 프로토콜의 메시지 포맷(JSON-RPC 2.0)을 준수하며, 메시지의 수신/송신을 담당한다.
- **Request Dispatcher**: 수신된 메시지의 `method`를 분석하여 `Tool Execution Path`로 보낼지, `Resource Access Path`로 보낼지 결정하는 라우팅 엔진이다.
- **Response Sequencer**: 각 경로에서 처리된 결과를 수집하여, 요청 시 부여된 `id`와 함께 프로토콜 규격에 맞는 응답 메시지를 생성한다.

### 2.2 도구 실행 경로 (Tool Execution Path)
에이전트의 명령을 실제 시스템 동작으로 변환하는 일련의 흐름이다.
- **Tool Registry**: 사용 가능한 도구의 목록, 설명, 파라미터 스키마를 관리하는 데이터 저장소이다.
- **Argument Validator**: `Tool Registry`의 스키마를 기반으로, 전달된 인자(arguments)의 타입, 필수 여부, 범위를 검증한다.
- **Command Translator**: 검증된 인자를 `Automation Wrapper`가 이해할 수 있는 구체적인 함수 호출 인자로 변환(Mapping)한다.
- **Execution Bridge**: 번역된 명령을 `Automation Wrapper`로 전달하고, 실행이 완료될 때까지 대기하거나 결과를 수집한다.

### 2.3 리소스 액세스 경로 (Resource Access Path)
시스템의 상태 정보를 에이전트가 읽을 수 있는 형태로 제공하는 흐름이다.
- **Resource URI Resolver**: 에이전트가 요청한 리소스 URI(예: `mcp://visual/screen`)를 분석하여 어떤 데이터 소스에 접근해야 하는지 결정한다.
- **Data Source Adapter**: `Visual State Manager`나 시스템 로그 등 외부 데이터 소스로부터 원시 데이터(Raw Data)를 가져오는 어댑터이다.
- **Format Encoder**: 가져온 원시 데이터를 MCP 리소스 규격(예: Base64 인코딩된 이미지, 텍스트)으로 변환하여 에이전트가 즉시 사용할 수 있게 만든다.

## 3. 컴포넌트 간 상호작용 (Inter-component Interaction)

### 3.1 도구 호출 흐름 (Tool Call Flow)
1. `JSON-RPC Interface` $\rightarrow$ `Request Dispatcher` (분기 결정)
2. `Request Dispatcher` $\rightarrow$ `Tool Execution Path` (Tool Call로 판단)
3. `Tool Execution Path` (`Registry` $\rightarrow$ `Validator` $\rightarrow$ `Translator` $\rightarrow$ `Bridge`)
4. `Execution Bridge` $\rightarrow$ `Automation Wrapper` (실행)
5. `Automation Wrapper` $\rightarrow$ `Response Sequencer` $\rightarrow$ `JSON-RPC Interface` $\rightarrow$ `Agent`

### 3.2 리소스 조회 흐름 (Resource Read Flow)
1. `JSON-RPC Interface` $\rightarrow$ `Request Dispatcher` (분기 결정)
2. `Request Dispatcher` $\rightarrow$ `Resource Access Path` (Resource Read로 판단)
3. `Resource Access Path` (`Resolver` $\rightarrow$ `Adapter` $\rightarrow$ `Encoder`)
4. `Encoder` $\rightarrow$ `Response Sequencer` $\rightarrow$ `JSON-RPC Interface` $\rightarrow$ `Agent`

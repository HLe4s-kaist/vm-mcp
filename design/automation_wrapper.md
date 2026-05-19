# Automation Wrapper 상세 설계 명세 (Detailed Design Specification)

## 1. 아키텍처 개요 (Architectural Overview)
Automation Wrapper는 MCP Server로부터 전달받은 추상적인 도구 명령을 실제 시스템 환경에서 실행 가능한 구체적인 명령으로 변환하고, 실행 과정의 안정성을 보장하는 핵심 로직 계층이다.

## 2. 컴포넌트 상세 설계 (Component Detail Design)

### 2.1 Command Orchestrator (명령 오케스트레이터)
전체 실행 흐름을 제어하고 각 하위 컴포넌트 간의 시퀀스를 관리한다.
- **Sequence Manager**: 도구 실행에 필요한 단계(좌표 변환 $\rightarrow$ 라이브러리 호출 $\rightarrow$ 결과 검증)를 순차적으로 제어한다.
- **State Monitor**: 현재 실행 중인 명령의 상태(IDLE, BUSY, ERROR)를 관리하여 중복 실행이나 비정상 종료를 방지한다.

### 2.2 Coordinate Transformation Engine (좌표 변환 엔진)
에이전트의 논리적 좌표계를 실제 물리적 디스플레이 좌표계로 매핑한다.
- **Resolution Resolver**: 현재 시스템의 디스플레이 해상도 및 스케일링(DPI) 정보를 실시간으로 파악한다.
- **Mapping Logic**: 에이전트가 사용하는 정규화된 좌표(예: 0.0~1.0) 또는 논리적 해상도를 기반으로 실제 픽셀 좌표를 계산한다.

### 2.3 Library Integration & Tool Execution (라이브러리 통합 및 도구 실행)
자동화 도구를 관리하고 실제 명령을 수행하는 계층이다.
- **Driver Registry & API**: `pyautogui`, `pynput` 등 사용 가능한 드라이버를 등록/관리하고, 통일된 API를 통해 명령을 전달한다.
- **Tool Delegation**: 관리되는 드라이버에게 변환된 명령(물리 좌표, 동작 등)을 위임하여 실제 시스템 동작을 수행하고 결과를 수집한다.

### 2.4 Execution Guard (실행 가드)
명령 실행 중 발생할 수 있는 환경적 변수와 예외 상황으로부터 시스템 안정성을 확보한다.
- **Environment Watcher**: 실행 직전 화면 해상도 변경, 권한 획득 실패, 포커스 유실 등의 환경 변화를 감지한다.
- **Exception Handler**: 실행 중 발생하는 라이브러리 오류나 시스템 예외를 포착하여, 이를 MCP 표준 에러 형식으로 변환하고 복구 프로세스를 트리거한다.

## 3. 상호작용 인터페이스 (Interaction Interfaces)

### 3.1 Upstream: MCP Server (상향 상호작용)
`MCP Server`와의 논리적 연결을 정의한다.
- **상호작용 주체**: `Automation Wrapper` (`Command Orchestrator`) $\leftrightarrow$ `MCP Server` (`Execution Bridge`)
- **상호작용 성격**: 
    - `Automation Wrapper`는 `MCP Server`로부터 전달받은 **구조화된 자동화 요청**을 수신하여 처리한다.
    - 처리 완료 후, **표준화된 실행 결과**를 `MCP Server`로 반환한다.
- **데이터 흐름**:
    - **수신 데이터**: 수행해야 할 동작의 의도와 필요한 실행 파라미터.
    - **반환 데이터**: 작업의 완결성(성공/실패), 결과 데이터, 그리고 필요 시 발생한 예외 정보.

### 3.2 Downstream: Visual State Manager (하향 상호작용)
`Visual State Manager`와의 논리적 연결을 정의한다.
- **상호작용 주체**: `Automation Wrapper` $\leftrightarrow$ `Visual State Manager`
- **상호작용 성격**: 
    - `Automation Wrapper`는 명령 실행 전후의 맥락 파악이나 좌표 검증을 위해 `Visual State Manager`에 **시각 데이터(스크린샷 등)를 요청**한다.
    - `Visual State Manager`는 요청된 시각 정보를 제공한다.
- **데이터 흐름**:
    - **요청 데이터**: 시각 정보 요청 유형 및 필요 범위.
    - **반환 데이터**: 캡처된 이미지 데이터 또는 시각적 메타데이터.

## 4. 컴포넌트 간 상호작용 흐름 (Inter-component Interaction)

### 4.1 도구 실행 프로세스 (Tool Execution Process)
1. **Trigger**: `Command Orchestrator`가 MCP Server로부터 실행 요청을 수신한다.
2. **Coordinate Mapping**: `Coordinate Transformation Engine`이 대상 좌표를 실제 픽셀 좌표로 변환한다.
3. **Driver Selection & Execution**: `Library Integration & Tool Execution` 계층에서 드라이버를 선택하고 명령을 위임하여 실행한다.
4. **Safety Check**: `Execution Guard`가 실행 전후의 환경 상태를 검증한다.
5. **Result Return**: 실행 완료 후 결과값(성공 여부, 데이터)을 `Command Orchestrator`를 통해 상위 계층으로 전달한다.

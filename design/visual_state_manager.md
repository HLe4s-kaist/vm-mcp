# Visual State Manager 상세 설계 명세 (Detailed Design Specification)

## 1. 아키텍처 개요 (Architectural Overview)
Visual State Manager는 시스템의 시각적 상태를 캡처, 관리 및 변환하여 MCP 에이전트와 모니터링 서비스에 유기적으로 제공하는 핵심 계층이다.

## 2. 컴포넌트 상세 설계 (Component Detail Design)

### 2.1 Capture Layer (캡처 계층)
시스템의 시각 정보를 원시 데이터 형태로 확보한다.
- **Environment Resolver**: 현재 시스템의 디스플레이 환경(물리/가상, 해상도, 스케일링)을 판별하여 최적의 캡처 방식을 결정한다.
- **Raw Data Capture**: 결정된 방식에 따라 픽셀 데이터 또는 비디오 프레임을 추출한다.

### 2.2 Processing Layer (처리 계층)
추출된 데이터를 목적에 맞는 형식으로 가공한다.
- **Image Formatter**: 캡처된 데이터를 MCP 리소스 규격에 맞는 이미지 포맷(PNG, JPEG 등)으로 인코딩하고 Base64로 변환한다.
- **Stream Transcoder**: 비디오 데이터를 실시간 모니터링을 위해 적절한 코덱(H.264 등)과 컨테이너로 변환한다.

### 2.3 Management Layer (관리 계층)
데이터의 효율적 관리와 안정적인 접근을 보장한다.
- **Resource Cache**: 최근 캡처된 데이터를 메모리에 유지하여 반복적인 리소스 요청에 대해 즉각적인 응답을 제공한다.
- **Access Synchronizer**: 다수의 요청(에이전트, 모니터링 브릿지)이 동시에 발생할 때 데이터 일관성을 유지하고 경합을 방지한다.

## 3. 상호작용 인터페이스 (Interaction Interfaces)

### 3.1 Upstream: Automation Wrapper (상향 상호작용)
`Automation Wrapper`와의 논리적 연결을 정의한다.
- **상호작용 주체**: `Visual State Manager` $\leftrightarrow$ `Automation Wrapper`
- **상호작용 성격**: 
    - `Automation Wrapper`가 명령 실행 전후의 맥락 파악이나 좌표 검증을 위해 `Visual State Manager`에 **시각 데이터(스크린샷 등)를 요청**한다.
    - `Visual State Manager`는 요청된 시각 정보를 제공한다.
- **데이터 흐름**:
    - **요청 데이터**: 시각 정보 요청 유형 및 필요 범위.
    - **반환 데이터**: 캡처된 이미지 데이터 또는 시각적 메타데이터.

### 3.2 Downstream: Monitoring Bridge (하향 상호작용)
`Monitoring Bridge`와의 논리적 연결을 정의한다.
- **상호작용 주체**: `Visual State Manager` $\leftrightarrow$ `Monitoring Bridge`
- **상호작용 성격**: 
    - `Visual State Manager`가 실시간 스트리밍을 위해 `Monitoring Bridge`에 **시각 데이터를 공급**한다.
    - `Monitoring Bridge`는 제공된 데이터를 외부로 중계한다.
- **데이터 흐름**:
    - **요청 데이터**: 스트리밍 시작/종료 신호 및 프로토콜 설정.
    - **반환 데이터**: 실시간으로 변환된 스트림 데이터(비디오 프레임).

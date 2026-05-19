# 작업 5: Automation Wrapper 상세 설계

## 목표
`Automation Wrapper` 컴포넌트에 대한 상세 기술 설계를 작성하고 `design/main.md`에 이를 포함시킨다.

## 단계
1. **`design/automation_wrapper.md` 생성**:
    - `Automation Wrapper`를 상호작용하는 서브 컴포넌트 집합으로 정의하여 아키텍처를 설계한다.
    - 포함할 서브 컴포넌트:
        - **Library Integration Layer**: 외부 자동화 라이브러리(예: `pyautogui`, OS 레벨 API)를 관리하고 호출한다.
        - **Coordinate Transformation Engine**: 에이전트의 논리적 좌표를 실제 스크린 좌표로 변환한다.
        - **Execution Guard/Safety Controller**: 예외 처리, 환경 변화(해상도, 권한 등) 대응 및 실행 안정성을 보장한다.
        - **Command Orchestrator**: 라이브러리 호출 시퀀스와 상태 전환을 관리한다.
    - 각 서브 컴포넌트에 대해 책임, 주요 기능, 데이터 흐름을 명시한다.
2. **`design/main.md` 수정**:
    - 2.2 섹션에 `design/automation_wrapper.md`로 연결되는 참조 링크를 추가한다.
3. **검증**:
    - `design/automation_wrapper.md`가 기술적으로 상세하게 작성되었는지 확인한다.
    - `design/main.md`의 링크가 정확한지 확인한다.

## 기대 결과물
기술적 깊이가 담긴 `design/automation_wrapper.md`와 연결이 완료된 `design/main.md`.

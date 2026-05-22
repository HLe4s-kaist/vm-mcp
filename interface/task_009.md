# 작업 9: Virtual Monitor 드래그 및 스크롤 마우스 이벤트 연동 및 프로젝트 완성

## 목표
- `src/templates/index.html` (Web Viewer 프론트엔드)에서 마우스 드래그, 이동, 스크롤 이벤트를 캡처하여 WebSocket으로 백엔드(`src/monitoring.py`)에 전송하는 기능을 구현합니다.
- 기존의 git commit 내역을 유지하며, 작업 단위별로 점진적인 git commit을 수행합니다.
- 프로젝트 전체 기능을 검증하기 위한 통합 테스트를 실행하고, 통과 여부를 확인합니다.
- `MEMORY.md` 및 `walkthrough.md`를 업데이트하여 프로젝트를 완수합니다.

## 상세 계획

### 1. 소스코드 수정 (`src/templates/index.html`)
- 기존의 단순 `click` 이벤트 리스너를 고도화하여 마우스 드래그 및 이동, 스크롤을 완벽히 지원하도록 합니다.
- **마우스 다운/업 (`mousedown`, `mouseup`)**:
  - 캔버스 내에서의 상대 좌표(0.0 ~ 1.0)를 계산하여 WebSocket으로 `mouse_down`, `mouse_up` 이벤트를 전송합니다.
- **마우스 이동 (`mousemove`)**:
  - 너무 잦은 메시지 전송을 방지하기 위해 50ms 스로틀링(Throttling)을 적용합니다.
  - 마우스 포인터가 캔버스 내부를 이동할 때 상대 좌표를 WebSocket으로 `mouse_move` 이벤트를 전송합니다.
- **마우스 스크롤 (`wheel`)**:
  - `wheel` 이벤트를 감지하여 휠 회전 방향(`e.deltaY`)에 따라 `scroll` 이벤트를 전송합니다. (음수 델타는 위로 스크롤 `pyautogui.scroll` 양수값, 양수 델타는 아래로 스크롤 음수값에 매핑)
  - 휠 동작 시 기본 브라우저 스크롤 현상을 방지하기 위해 `e.preventDefault()`를 수행합니다.

### 2. 점진적 Git 커밋 수행 (중간 커밋 요구사항 충족)
- **1단계 커밋**: 현재 수정되어 미커밋 상태인 백엔드 드래그/스크롤 코드(`src/automation.py`, `src/monitoring.py`)를 먼저 커밋합니다.
  - 커밋 메시지: `feat: add mouse drag, move, and scroll handlers in automation and monitoring backend`
- **2단계 커밋**: `src/templates/index.html` 수정 완료 후 커밋합니다.
  - 커밋 메시지: `feat: implement mouse drag, move, and scroll event listeners in Web Viewer UI`
- **3단계 커밋**: 문서 및 마무리 작업 커밋.
  - 커밋 메시지: `docs: update MEMORY.md and walkthrough.md for project completion`

### 3. 검증 계획
- **자동화 테스트 실행**:
  - `python3 tests/test_run.py` 실행: 웹 서버 정상 동작 및 포트 바인딩 확인.
  - `python3 tests/test_mcp.py` 실행: MCP stdio JSON-RPC 도구 동작 확인.
- **수동 검증**:
  - 테스트 로그 상 에러 여부를 모니터링하여 전체 컴포넌트가 연동되는지 체크.

## 승인 요청
위 계획에 대해 승인을 요청합니다. 승인 후 작업을 진행하겠습니다.

# 리팩토링 계획: VNC 지원, Windows 호환 및 스크린샷 파일 관리

본 문서에서는 X11(Xvfb) 기반의 기존 가상 모니터 기능을 VNC 기반으로도 유사하게 작동하도록 리팩토링하고, Windows 환경 지원 및 스크린샷 파일 용량 관리 기능을 추가하는 계획을 정의합니다.

## 1. 현재 구조 분석
- **가상 디스플레이**: Linux 환경에서 Xvfb를 실행하여 `:98` 또는 `:99` 디스플레이 번호에서 X 서버 구동.
- **화면 캡처 & 자동화**: `mss`/`pyautogui`를 사용하여 로컬 화면(X11 디렉션) 제어 및 캡처.
- **제한점**: Xvfb와 X11 관련 라이브러리 의존성으로 인해 Windows 환경에서 구동 불가.

## 2. 변경 목표 및 상세 설계

### A. VNC 지원 및 통합 자동화 인터페이스
- `automation_mode` 설정 도입 (`local` 또는 `vnc`).
- **Local 모드**:
  - 기존 방식 유지 (Linux에서는 Xvfb 구동, Windows에서는 Xvfb 없이 실행).
- **VNC 모드**:
  - `asyncvnc` 라이브러리를 사용하여 원격/로컬 VNC 서버에 연결.
  - VNC 클라이언트를 통해 화면 프레임 버퍼 수신 및 마우스/키보드 이벤트 송신.
  - Xvfb 프로세스를 시작하지 않으므로 플랫폼 독립적 작동 가능.

### B. Windows 호환성 확보
- `src/main.py`에서 OS가 Windows(`sys.platform == "win32"`)이거나 `automation_mode == "vnc"`인 경우 Xvfb 시작 생략.
- `pyautogui` 및 `mss`가 Windows에서 기본 구동되므로, Local 모드를 Windows에서 실행 시 시스템의 기본 디스플레이 제어 가능.

### C. 스크린샷 파일 관리 및 자동 로테이션
- 스크린샷 저장 디렉토리 `screenshot.save_dir` (기본값: `~/.config/vmvm/`) 및 최대 용량 `screenshot.max_size_mb` (기본값: 100MB) 설정 추가.
- MCP `screenshot` 도구 호출 또는 웹 UI를 통해 스크린샷 저장 시 지정된 디렉토리에 파일 저장.
- 저장소 정리 로직:
  - 지정 경로 내의 `screenshot_*.*` 파일들을 조회하여 총 크기 계산.
  - 총 크기가 `max_size_mb`를 초과하면 수정 시간이 오래된 파일부터 순차적으로 삭제.
  - 다른 설정 파일(`config.json` 등)을 건드리지 않도록 파일명 패턴 매칭 적용.

### D. Web UI 및 API 확장
- **추가 API 엔드포인트**:
  - `GET /api/screenshots`: 스크린샷 파일 통계 (총 용량, 최대 용량, 파일 목록 등) 반환.
  - `POST /api/screenshots/clear`: 저장된 모든 스크린샷 파일 삭제.
  - `POST /api/screenshots/capture`: 현재 화면을 즉시 캡처하여 파일로 저장 및 결과 반환.
- **Web UI 변경**:
  - 실시간 뷰어 하단에 "스크린샷 저장소 관리" 섹션 추가.
  - 현재 사용 용량 / 최대 용량 및 파일 개수 시각화.
  - 최대 용량 설정 입력(MB 단위) 및 변경값 반영.
  - "즉시 캡처(Capture)", "모두 비우기(Clear All)" 버튼 탑재.

---

## 3. 세부 변경 사항 (대상 파일)

### `src/config.py`
- 기본 설정에 `automation_mode`, `vnc` 세부 정보 및 `screenshot` 정보 추가.
- default:
  ```json
  "automation_mode": "local",
  "vnc": {
      "host": "127.0.0.1",
      "port": 5900,
      "password": ""
  },
  "screenshot": {
      "save_dir": "~/.config/vmvm/",
      "max_size_mb": 100
  }
  ```

### `src/vnc_manager.py` [NEW]
- `asyncvnc`를 감싸서 비동기 연결 관리 및 자동 재연동 수행.
- 스크린샷 수집, 마우스 클릭/드래그/이동/휠 스크롤, 키 입력/텍스트 입력을 비동기적으로 처리하고 동기 API와 호환되도록 래핑 제공.

### `src/main.py`
- Windows 혹은 VNC 모드 시 Xvfb 실행 생략 조건식 추가.
- `VNCManager` 초기화 및 웹 서버와 동일한 백그라운드 이벤트 루프에 등록.

### `src/automation.py`
- `execute_command` 메서드 리팩토링: `automation_mode`에 따라 `pyautogui` 또는 `VNCManager` 호출 분기.
- PyAutoGUI 키 이름을 VNC Keysym 이름으로 맵핑하는 변환기 정의.

### `src/visual_state.py`
- `capture_screen` 리팩토링: VNC 모드인 경우 `VNCManager`로부터 캡처 데이터 수집.
- 스크린샷 파일 저장, 자동 용량 계산 및 오래된 스크린샷 자동 삭제 로직 구현.

### `src/monitoring.py`
- 새로운 API 엔드포인트 `/api/screenshots`, `/api/screenshots/clear`, `/api/screenshots/capture` 등록 및 처리 로직 추가.

### `src/templates/index.html`
- 수려한 스타일링을 적용한 스크린샷 저장소 관리 패널 마크업 및 JS 인터랙션 연동.

---

## 4. 검증 계획
1. **단위 테스트 및 시나리오 검증**:
   - `tests/test_run.py`, `tests/test_mcp.py` 등이 정상 작동하는지 확인.
   - VNC 모드 시뮬레이션 작동 확인.
2. **저장소 로테이션 검증**:
   - 스크린샷을 임의로 다수 생성하여 최대 용량을 초과할 때 가장 오래된 파일이 삭제되는지 테스트 스크립트 작성 및 실행.
3. **Windows 호환 검증**:
   - Windows 감지 코드 검증.

# 프로젝트 메모리

## 진행 상황
- [x] design/main.md 생성 (최종 설계안 확정)
- [x] design/mcp_server.md 생성 및 재설계 (컴포넌트 분해 및 구조화)
- [x] design/visual_state_manager.md 생성 및 재설계 (상향/하향 상호작용 구조 적용)
- [x] design/main.md에 Configuration Manager 컴포넌트 추가
- [x] src/ 디렉토리에 모든 핵심 컴포넌트 및 Web Viewer 구현 완료 (Task 8)
- [x] tests/ 디렉토리에 기본 검증 및 MCP 프로토콜 통합 테스트 작성 및 패스 (Task 8)
- [x] Web Viewer UI 드래그, 이동 및 마우스 휠 스크롤 연동 완료 (Task 9)
- [x] MCP 기능 전면 리팩토링: 깨진 SSE 몽키패치 전부 제거, streamable-http 전송 추가 (Task 16)
- [x] MCP 로컬(stdio) 및 원격(streamable-http) 전송 모두 검증 완료 (Task 16)
- [x] 불필요한 SSE 테스트 파일 삭제 및 streamable-http 통합 테스트 작성 (Task 16)
- [x] README.md 전면 재작성: SSH/SSE 관련 잘못된 가이드 제거, 정확한 연동 가이드 작성 (Task 16)
- [x] README.md 개선 및 영어 README.en.md 추가, AI 면책 조항 명시 (Task 17)
- [x] 라이선스 파일 생성 및 GPLv2 라이선스 설정 (Task 17)
- [x] 리팩토링 완료: VNC 지원, Windows 호환 및 스크린샷 파일 용량 관리 및 자동 로테이션 구현 (Task 18)
- [x] VNC 기능 완전 수정 및 검증: asyncvnc API 호환성 수정, RGBA→RGB 변환, CLI 인수 추가, 종합 통합 테스트 작성 (Task 19)

## 설계 문서
- [design/main.md](./design/main.md): 시스템 전체 설계 (Existing Tools를 활용한 MCP Wrapping 구조)
- [design/mcp_server.md](./design/mcp_server.md): MCP Server - 상세 설계 (컴포넌트 분해 설계)
- [design/automation_wrapper.md](./design/automation_wrapper.md): Automation Wrapper - 상세 설계 (통합 컴포넌트 및 상호작용 구조)
- [design/visual_state_manager.md](./design/visual_state_manager.md): Visual State Manager - 상세 설계 (상향/하향 상호작용 구조 적용)
- [interface/vnc_refactoring.md](./interface/vnc_refactoring.md): VNC 지원 및 스크린샷 파일 관리 리팩토링 계획

## 소스코드 및 검증 파일
- [LICENSE](./LICENSE): GPLv2 라이선스 전문
- [README.md](./README.md): 프로젝트 메인 한국어 리드미
- [README.en.md](./README.en.md): 프로젝트 메인 영어 리드미
- [src/main.py](./src/main.py): 시스템 진입점 및 가상 디스플레이(Xvfb) 제어 오케스트레이션
- [src/config.py](./src/config.py): 중앙 설정 관리 컴포넌트
- [src/visual_state.py](./src/visual_state.py): 스크린 캡처 및 포맷 인코더 컴포넌트
- [src/automation.py](./src/automation.py): PyAutoGUI 래핑 및 좌표 변환/보호 장치 컴포넌트
- [src/monitoring.py](./src/monitoring.py): Starlette/Uvicorn 기반 실시간 웹/웹소켓 관찰 브릿지 컴포넌트
- [src/templates/index.html](./src/templates/index.html): 프리미엄 반응형 실시간 모니터 및 컨트롤 웹 UI
- [src/mcp_server.py](./src/mcp_server.py): FastMCP API 기반 AI 에이전트 연동 도구 및 리소스 컴포넌트 (stdio + streamable-http 지원)
- [src/vnc_manager.py](./src/vnc_manager.py): asyncvnc 기반 VNC 연결 및 원격 제어 관리 컴포넌트
- [tests/test_run.py](./tests/test_run.py): 시스템 및 웹 서버 기본 포트/경로 응답 테스트
- [tests/test_mcp.py](./tests/test_mcp.py): MCP JSON-RPC 2.0 프로토콜 초기화 및 도구 동작 통합 테스트
- [tests/test_mcp_sdk_client.py](./tests/test_mcp_sdk_client.py): MCP SDK stdio 클라이언트를 통한 전체 도구/리소스 통합 테스트
- [tests/test_interaction.py](./tests/test_interaction.py): WebSocket을 통한 드래그/스크롤 마우스 인터랙션 이벤트 연동 통합 테스트
- [tests/test_streamable_http.py](./tests/test_streamable_http.py): Streamable HTTP 원격 MCP 전송 및 도구 호출 통합 테스트
- [tests/test_screenshot_storage.py](./tests/test_screenshot_storage.py): 스크린샷 저장소 용량 제한 및 로테이션 자동 삭제 통합 테스트
- [tests/test_vnc_integration.py](./tests/test_vnc_integration.py): VNC 모드 종합 통합 테스트 (연결, 스크린샷, 마우스, 키보드, 웹 서버, MCP)

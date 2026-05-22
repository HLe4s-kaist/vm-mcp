# 프로젝트 메모리

## 진행 상황
- [x] design/main.md 생성 (최종 설계안 확정)
- [x] design/mcp_server.md 생성 및 재설계 (컴포넌트 분해 및 구조화)
- [x] design/visual_state_manager.md 생성 및 재설계 (상향/하향 상호작용 구조 적용)
- [x] design/main.md에 Configuration Manager 컴포넌트 추가
- [x] src/ 디렉토리에 모든 핵심 컴포넌트 및 Web Viewer 구현 완료 (Task 8)
- [x] tests/ 디렉토리에 기본 검증 및 MCP 프로토콜 통합 테스트 작성 및 패스 (Task 8)
- [x] Web Viewer UI 드래그, 이동 및 마우스 휠 스크롤 연동 완료 (Task 9)
- [x] 외부 에이전트 연동을 위한 MCP SSE(HTTP) 네트워크 서버 기능 구현 및 테스트 완료 (Task 9)
- [x] MCP SSE /sse 엔드포인트 직접 POST/DELETE 수신 시 405 Method Not Allowed 문제 해결 및 테스트 완료 (Task 10)
- [x] README.md 에 외부 에이전트 SSE 연동 및 몽키 패치 설명 가이드 업데이트 완료 (Task 10)
- [x] session_id 누락 클라이언트 대응 활성 세션 자동 매핑 폴백 구현 및 테스트 완료 (Task 11)
- [x] 외부 SSE 에이전트 연동을 위한 상세 가이드 보완 및 실전 파이썬 테스트 클라이언트 스크립트 제공 완료 (Task 12)

## 설계 문서
- [design/main.md](./design/main.md): 시스템 전체 설계 (Existing Tools를 활용한 MCP Wrapping 구조)
- [design/mcp_server.md](./design/mcp_server.md): MCP Server - 상세 설계 (컴포넌트 분해 설계)
- [design/automation_wrapper.md](./design/automation_wrapper.md): Automation Wrapper - 상세 설계 (통합 컴포넌트 및 상호작용 구조)
- [design/visual_state_manager.md](./design/visual_state_manager.md): Visual State Manager - 상세 설계 (상향/하향 상호작용 구조 적용)

## 소스코드 및 검증 파일
- [src/main.py](./src/main.py): 시스템 진입점 및 가상 디스플레이(Xvfb) 제어 오케스트레이션
- [src/config.py](./src/config.py): 중앙 설정 관리 컴포넌트
- [src/visual_state.py](./src/visual_state.py): 스크린 캡처 및 포맷 인코더 컴포넌트
- [src/automation.py](./src/automation.py): PyAutoGUI 래핑 및 좌표 변환/보호 장치 컴포넌트
- [src/monitoring.py](./src/monitoring.py): Starlette/Uvicorn 기반 실시간 웹/웹소켓 관찰 브릿지 컴포넌트
- [src/templates/index.html](./src/templates/index.html): 프리미엄 반응형 실시간 모니터 및 컨트롤 웹 UI
- [src/mcp_server.py](./src/mcp_server.py): FastMCP API 기반 AI 에이전트 연동 도구 및 리소스 컴포넌트
- [tests/test_run.py](./tests/test_run.py): 시스템 및 웹 서버 기본 포트/경로 응답 테스트
- [tests/test_mcp.py](./tests/test_mcp.py): MCP JSON-RPC 2.0 프로토콜 초기화 및 도구 동작 통합 테스트
- [tests/test_interaction.py](./tests/test_interaction.py): WebSocket을 통한 드래그/스크롤 마우스 인터랙션 이벤트 연동 통합 테스트
- [tests/test_sse.py](./tests/test_sse.py): MCP 서버 HTTP SSE 네트워크 노출 및 연동 통합 테스트
- [tests/test_sse_monkeypatch.py](./tests/test_sse_monkeypatch.py): MCP 서버 SSE 몽키패칭 호환성(OPTIONS, POST, DELETE) 검증 테스트
- [tests/test_sse_client.py](./tests/test_sse_client.py): 외부 SSE 클라이언트 에이전트 연동 시뮬레이션 및 검증 테스트

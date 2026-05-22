# Task 015: SSE MCP 연결 장애 및 OAuth 404 차단 해결, 세션 라이프사이클 안정화 및 README.md 가이드 보완 계획

## 1. 배경 및 현상 분석
현재 외부 에이전트(예: 최신 Claude Desktop)가 본 MCP 서버의 SSE(Server-Sent Events) 모드로 연결을 시도할 때 다음과 같은 연결 장애 원인들이 식별되었습니다:

1. **OAuth Discovery 404 에러로 인한 연결 거부**:
   - 최신 Claude Desktop과 같은 MCP 클라이언트 SDK는 최초 `GET /sse` 연결을 시작하기 전에 `GET /.well-known/oauth-protected-resource` 및 `GET /.well-known/oauth-protected-resource/sse` 경로로 인증 메타데이터 조회를 시도합니다.
   - 서버가 이 경로에 대해 `404 Not Found`를 반환하면 클라이언트는 보안 인증 과정 실패로 규정하고 연결 시도 전체를 중단해버립니다.
2. **세션 만료/연결 해제 시 Stale Session 누수**:
   - `SseServerTransport.connect_sse` 컨텍스트 매니저 내부에서 생성된 `session_id`가 클라이언트 연결 종료 시 `self._read_stream_writers` 목록에서 삭제(pop)되지 않고 남아있습니다.
   - 이로 인해 클라이언트 재접속이나 다른 클라이언트 요청 처리 시, 서버가 이미 끊어진 죽은(Stale) 세션을 유효한 세션으로 인식하여 잘못된 세션으로 POST 요청을 라우팅해 silent packet loss가 발생합니다.
3. **CORS OPTIONS Preflight 요청 처리 실패**:
   - 브라우저나 크로스 오리진 샌드박스 환경의 클라이언트가 `/messages/` 경로로 POST 요청을 보내기 전 전송하는 `OPTIONS` 예비 요청이 body가 없어 JSON-RPC 파싱 유효성 검증(ValidationError)을 거치며 `400 Bad Request` 에러를 응답받게 됩니다.
4. **PyAutoGUI Linux 환경 Warning 로그 누적**:
   - 리눅스 headless 환경에서 `pyautogui.getActiveWindow()` 호출 시 AttributeError가 발생하며 매번 예외 처리가 발생해 불필요한 에러 로그를 대량으로 출력합니다.

---

## 2. 해결 계획

### 2.1. `src/mcp_server.py` 보완 (SSE 몽키패치 강화)
1. **OAuth Discovery 더미 엔드포인트 추가**:
   - Starlette `app.routes`에 `GET` 및 `OPTIONS`를 수신하는 `/.well-known/oauth-protected-resource` 및 `/.well-known/oauth-protected-resource/sse` 더미 라우트를 등록합니다.
   - 클라이언트 탐색 시 `200 OK` 응답과 함께 빈 JSON 객체 `{}` 및 CORS 헤더를 전달하도록 구현합니다.
2. **SseServerTransport.connect_sse 패치 (Stale Session 방지)**:
   - `connect_sse` 비동기 제너레이터를 몽키 패칭하여, 컨텍스트 매니저가 종료되는 `finally` 시점에 `self._read_stream_writers.pop(session_id, None)`을 실행하도록 보완합니다.
   - 이를 통해 클라이언트 분리 시 관련 세션 정보를 즉시 제거하여 활성 세션 자동 매핑 풀백(`get_active_session()`)이 항상 유효한 세션만 바라보도록 안전하게 보장합니다.
3. **SseServerTransport.handle_post_message 패치 (OPTIONS CORS Preflight 대응)**:
   - `handle_post_message` ASGI 메서드를 몽키 패칭하여, `OPTIONS` 메서드로 들어오는 Preflight 요청을 감지하면 즉시 적절한 CORS 헤더와 함께 `204 No Content` (또는 `200 OK`)를 응답하고 실행을 종료합니다.
   - 이로써 JSON-RPC 바디 검증 단계를 안전하게 스킵하고 브라우저 CORS 보안 검증을 통과하도록 합니다.

### 2.2. `src/visual_state.py` 보완
- `pyautogui.getActiveWindow` 메소드 유무를 `hasattr(pyautogui, "getActiveWindow")`로 사전 체크하여 AttributeError 발생을 원천적으로 차단하고 로그를 깔끔하게 유지합니다.

### 2.3. `README.md` 가이드 보완
- 한국어 사용자 설정 설명 가이드에 최신 Claude Desktop 등 SSE MCP 외부 에이전트의 연동 실패 시 조치 방법(재시작 필요성 등)과 원인 분석 내용을 보강하여 상세하게 업데이트합니다.

---

## 3. 검증 계획
1. **단위 및 통합 테스트 검증**:
   - `python3 tests/test_sse_monkeypatch.py` 및 `python3 tests/test_sse_client.py`를 수행하여 OPTIONS 요청, 세션 자동 매핑, POST/DELETE 작동 상태를 검증합니다.
2. **새로운 테스트 시나리오 구현**:
   - `tests/test_sse_monkeypatch.py`에 OAuth 404 해결에 관한 테스트(더미 엔드포인트 GET 및 OPTIONS 요청 테스트)를 새로 추가하여 자동화 검증을 한층 더 단단하게 구축합니다.

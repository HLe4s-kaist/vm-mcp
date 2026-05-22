# Task 010: MCP SSE POST/DELETE 405 Method Not Allowed 문제 해결 계획 및 결과

## 배경 및 현상
- 외부 에이전트(클라이언트)가 연동 테스트 중 `POST /sse` 및 `DELETE /sse` 요청을 보냈으나, 서버측에서 `405 Method Not Allowed`가 발생함.
- 이전 작업에서 `/sse` 경로로 들어오는 POST/DELETE를 `/messages/`로 라우팅하는 몽키 패치를 적용하였으나 여전히 405 에러가 발생함.

## 원인 분석
1. **마운트 경로 불일치**: 몽키 패치 내에서 `/messages` 마운트를 찾을 때 `r.path == "/messages"`를 검사하고 있으나, FastMCP의 실제 메시지 마운트 경로는 `"/messages/"` (trailing slash 포함)이기 때문에 조건문이 실행되지 않아 몽키 패치가 아예 등록되지 않음.
2. **Double Response 위험**: 몽키 패치 내부에서 `post_message_app`을 직접 호출(await)한 후 Starlette의 `Response()`를 반환하면, 이미 HTTP 응답이 전송된 상태에서 Uvicorn이 추가적인 Response 처리를 시도하여 ASGI 프로토콜 예외(Double Response)가 발생할 위험이 있음.
3. **DELETE 요청 처리 미흡**: `DELETE` 요청 시에는 JSON-RPC 메시지 바디가 없으므로 `handle_post_message`로 그대로 흘려보내면 JSON validation error(400)가 발생할 수 있음. 따라서 `DELETE` 요청 시에는 세션 스트림을 명시적으로 안전하게 닫아주는 처리가 필요함.

## 해결 계획 및 실제 구현 내용

### 1. 마운트 경로 매칭 보완
- `r.path == "/messages"` 검사 대신 `r.path.startswith("/messages")`로 교체하여 `/messages/` 등 다양한 형태에도 정상 동작하도록 수정.
- 수정 파일: [src/mcp_server.py](file:///root/proj/vmvm/src/mcp_server.py)

### 2. NullResponse 구현
- 이미 응답을 전송한 뒤 Starlette이 추가 응답을 보내 에러를 내지 않도록 아무 작업도 하지 않는 `NullResponse` 클래스를 생성하여 반환함.
- 수정 파일: [src/mcp_server.py](file:///root/proj/vmvm/src/mcp_server.py)

### 3. DELETE 요청에 대한 명시적 세션 정리
- `DELETE` 요청이 올 경우, 쿼리 스트링의 `session_id`를 파싱하여 `SseServerTransport`의 `_read_stream_writers`에서 세션 writer를 찾아 닫고 삭제한 후 `Response("Accepted", status_code=202)`를 반환하도록 처리.
- 수정 파일: [src/mcp_server.py](file:///root/proj/vmvm/src/mcp_server.py)

### 4. 로컬 재현 및 연동 테스트 구현
- `/sse`로 `POST` 및 `DELETE` 요청을 보내 405 Method Not Allowed 없이 성공적으로 처리(CORS 헤더 및 status_code 200대)되는지 검증하는 단위 테스트 추가.
- 신규 파일: [tests/test_sse_monkeypatch.py](file:///root/proj/vmvm/tests/test_sse_monkeypatch.py)
- 실행 결과: **통과 (Success)**
  - OPTIONS, POST, DELETE 요청에 대해 각각 `200 OK`, `404 Not Found (Could not find session)`, `202 Accepted`로 405 예외 없이 라우팅이 우회 및 처리됨을 확인.

### 5. 기존 테스트 무결성 유지 검증
- `tests/test_run.py` (통과)
- `tests/test_mcp.py` (통과, python-xlib 경고 로그 출력 시 readline 블로킹 이슈 방지를 위해 JSON-RPC 포맷만 골라 파싱하는 읽기 루프로 로버스트하게 수정함)
- `tests/test_interaction.py` (통과)
- `tests/test_sse.py` (통과)

## README.md 업데이트
- [README.md](file:///root/proj/vmvm/README.md)에 몽키 패치 적용 사항(POST/DELETE/OPTIONS 직접 허용) 및 외부 클라이언트 연결을 위한 안내 가이드, `test_sse_monkeypatch.py` 구동 방법을 명시적으로 기재함.

# Task 013: SSE 전역 세션 관리 안정화 및 상세 요청 로깅 미들웨어 장착

## 배경 및 현상
- 외부 클라이언트가 `POST /sse` 요청 시 `400 Bad Request` 에러를 계속 겪고 있음.
- 서버 측에서는 `Received POST request without session_id and no active SSE session exists.` 경고가 뜸.
- 이는 두 가지 원인 중 하나일 가능성이 높음:
  1. 클라이언트(예: Claude Desktop)가 이전에 맺은 세션 정보를 캐싱하여 사용하는데, 서버 재시작 후 세션을 재수립(GET /sse)하지 않고 POST만 보내는 경우.
  2. Starlette 라우팅 미들웨어 래핑으로 인해 `post_message_app.__self__` 리플렉션이 실패하여 활성 세션 목록(`_read_stream_writers`)을 찾지 못하는 경우.

## 해결 계획 및 실제 구현 내용

### 1. SseServerTransport 전역 인스턴스 추적 패치
- `SseServerTransport.__init__`을 몽키 패칭하여 생성되는 모든 인스턴스를 글로벌 리스트 `active_transports`에 등록합니다.
- `post_message_app.__self__` 참조 방식 대신, `active_transports` 리스트를 역순으로 순회하여 활성화된 세션 ID(`target_session_id`)를 100% 안전하게 탐색하고 맵핑하도록 보완합니다.

### 2. 친절한 400 Bad Request 안내 메시지 리턴
- `session_id`가 없고 서버에 활성 세션이 하나도 없는 비정상 상황에서, 단순 400 에러 대신 다음과 같은 자세한 메시지를 반환합니다:
  `"Bad Request: No active SSE session found. Please establish a GET /sse connection first, or restart your client agent to refresh the session."`
- 이를 통해 클라이언트(Claude Desktop 등) 재시작이 필요함을 사용자에게 직접적으로 알립니다.

### 3. HTTP 요청/응답 상세 로깅 미들웨어(RequestLoggingMiddleware) 장착
- Starlette 앱에 모든 HTTP 요청 및 응답 상태 코드를 로깅하는 ASGI 미들웨어를 장착합니다.
- 이로써 `GET /sse` 연결 상태, `POST` 진행 과정, 그리고 최종 응답 코드까지 Uvicorn 로그에 투명하게 출력되도록 하여 디버깅 가독성을 비약적으로 높입니다.

## 승인 요청
- 위 계획에 대해 승인을 요청합니다. 승인 후 작업을 수행하겠습니다.

# Task 014: OAuth 메타데이터 404 차단 해결 및 SSE 연결 수립 안정화 계획

## 1. 배경 및 현상 분석
현재 외부 에이전트(192.168.183.200)가 연결 시 다음과 같은 실패 로그를 보이고 있습니다:
```
2026-05-22 07:18:27,752 - [WARNING] - root - Received POST request without session_id and no active SSE session exists.
2026-05-22 07:18:27,752 - [WARNING] - mcp.server.sse - Received request without session_id
INFO:     192.168.183.200:48534 - "POST /sse HTTP/1.1" 400 Bad Request
INFO:     192.168.183.200:48534 - "DELETE /sse HTTP/1.1" 202 Accepted
INFO:     192.168.183.200:37196 - "GET /.well-known/oauth-protected-resource/sse HTTP/1.1" 404 Not Found
INFO:     192.168.183.200:37196 - "GET /.well-known/oauth-protected-resource HTTP/1.1" 404 Not Found
```

이 로그에서 알 수 있는 핵심 쟁점은 다음과 같습니다:
1. **GET /sse 연결 부재**: 클라이언트 측에서 새로운 SSE 스트림을 수립하는 `GET /sse` 요청이 아예 도달하지 못하고 있습니다.
2. **OAuth 메타데이터 404 오류**: 클라이언트 라이브러리가 보안 및 토큰 검증 여부를 확인하기 위해 `GET /.well-known/oauth-protected-resource` 및 `GET /.well-known/oauth-protected-resource/sse`를 호출하고 있습니다. 하지만 서버는 이 경로에 대한 정의가 없어 `404 Not Found`를 뱉고 있으며, 이로 인해 클라이언트가 인증 단계 실패로 판단하여 더 이상의 연결 진행(`GET /sse`)을 시도하지 않고 연결 프로세스를 종료(중단)하는 것으로 파악됩니다.
3. **이전 세션 캐싱 및 POST 직발송**: 클라이언트 측에 이전 세션 정보나 잘못된 POST 경로가 캐싱되어 있어, 재연결 실패 상태에서 툴을 실행할 때마다 `POST /sse`가 바로 전송되어 `400 Bad Request`가 반복 발생하고 있습니다.

## 2. 해결 계획

### 2.1. OAuth Discovery/Protected Resource 404 해결 (더미 라우트 등록)
FastMCP 인스턴스의 Starlette 앱에 다음 두 경로를 추가하여 `404 Not Found` 대신 성공 응답(`200 OK` 및 빈 JSON `{}`)을 주도록 몽키패치를 보완합니다.
- `GET /.well-known/oauth-protected-resource`
- `GET /.well-known/oauth-protected-resource/sse`
이로써 클라이언트가 인증 메타데이터 확인 단계를 에러 없이 통과하고 정상적으로 `GET /sse` 연결을 맺을 수 있도록 유도합니다.

### 2.2. 로깅 가시성 확보 및 오류 검증 강화
- Uvicorn 로그 레벨에 구애받지 않고 유저가 연결 상태를 실시간으로 인지할 수 있도록, `sys.stderr`에 명확하게 찍히는 로그 출력을 `print(..., file=sys.stderr, flush=True)` 형식으로 보완합니다.
- `RequestLoggingMiddleware`가 모든 HTTP 요청/응답 코드와 헤더를 출력하게 하여 디버깅 정보의 질을 높입니다.

### 2.3. README.md 가이드 보완
- 클라이언트 측(Cursor, Claude Desktop 등)의 세션 캐싱으로 인한 연결 장애 시 **클라이언트 재시작**이 필수적임을 명시하고, 연동 설정 방법 및 트러블슈팅 가이드를 `README.md`에 확실하게 담아 유저가 직관적으로 대처할 수 있도록 합니다.

## 3. 승인 요청
위의 분석 내용과 해결 계획에 대해 승인을 요청합니다. 승인을 받으면 작업을 수행하여 코드를 수정하고 검증 테스트를 진행하겠습니다.

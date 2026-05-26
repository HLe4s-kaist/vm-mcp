# Task 016: MCP 기능 전면 리팩토링 — SSE 제거, streamable-http 추가

## 요청 내용
- MCP 기능이 제대로 동작하지 않음 → 기능 완성
- 로컬(stdio) 먼저 구현/검증 → 원격(HTTP) 확장
- 기존 SSE 몽키패치 및 SSH 가이드 제거

## 수행 결과

### 변경 파일
1. **src/mcp_server.py**: SSE 몽키패치 ~200줄 전부 제거, streamable-http 전송 추가 (403줄→190줄)
2. **src/main.py**: CLI `--mcp-transport`에 `streamable-http` 옵션 추가
3. **tests/test_streamable_http.py**: [신규] 원격 HTTP MCP 통합 테스트
4. **tests/test_mcp_sdk_client.py**: [신규] MCP SDK stdio 클라이언트 전체 도구 통합 테스트
5. **tests/test_sse.py**: [삭제]
6. **tests/test_sse_monkeypatch.py**: [삭제]
7. **tests/test_sse_client.py**: [삭제]
8. **README.md**: SSH/SSE 가이드 제거, streamable-http 연동 가이드로 전면 재작성
9. **MEMORY.md**: 진행 상황 업데이트

### 검증 결과
- test_run.py: ✅ PASS
- test_mcp.py: ✅ PASS  
- test_mcp_sdk_client.py: ✅ PASS (12개 도구 + 리소스 전부 검증)
- test_interaction.py: ✅ PASS
- test_streamable_http.py: ✅ PASS (12개 도구 + 리소스 전부 검증)

## 상태: 완료 ✅

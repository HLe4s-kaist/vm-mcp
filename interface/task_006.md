# 작업 6: Visual State Manager 상세 설계

## 목표
`design/main.md`의 2.3 섹션에 명시된 `Visual State Manager`의 상세 기술 설계를 `design/visual_state_manager.md`에 작성하고, `design/main.md`에 이를 포함시킨다.

## 단계
1. **`design/visual_state_manager.md` 생성**:
    - `Visual State Manager`를 구성하는 핵심 서브 컴포넌트들의 상세 설계를 작성한다.
    - 포함할 서브 컴포넌트:
        - **Capture Engine**: 화면 데이터를 추출하는 메커니즘 (스크린샷, 가상 디스플레이 API 등).
        - **Format Converter**: 추출된 데이터를 MCP 리소스용(이미지) 또는 스트리밍용(비디오/인코딩 데이터)으로 변환하는 로직.
        - **State Buffer/Cache**: 잦은 캡처 요청에 대응하기 위한 데이터 관리 및 캐싱 전략.
    - 각 컴포넌트의 책임, 기능, 데이터 흐름을 기술한다.
2. **`design/main.md` 수정**:
    - 2.3 섹션에 `design/visual_state_manager.md`로 연결되는 참조 링크를 추가한다.
3. **검증**:
    - `design/visual_state_manager.md`의 기술적 완성도를 확인한다.
    - `design/main.md`의 링크가 올바른지 확인한다.

## 기대 결과물
기술적 깊이가 담긴 `design/visual_state_manager.md`와 연결이 완료된 `design/main.md`.

# Tool Mapping 설계 명세 (Tool Mapping Design Specification)

## 1. 설계 목표 (Design Goals)
Tool Mapping 컴포넌트는 MCP 요청을 내부 실행 단위로 변환하는 과정에서 발생하는 복잡성을 격리하고, 에이전트의 추상적 호출을 구체적인 실행 명령으로 정제하는 것을 목표로 한다. 본 설계는 단일 책임 원칙(SRP)에 따라 기능을 최소 단위의 컴포넌트로 분해하여 확장성과 테스트 용이성을 확보한다.

## 2. 컴포넌트 분해 (Component Decomposition)

### 2.1 Registry Manager (등록 관리자)
도구의 메타데이터와 실제 실행 객체를 관리하는 최소 단위 컴포넌트이다.
- **Identifier Map**: 도구의 논리적 명칭(String)과 내부 실행 식별자(Internal ID) 간의 매핑 정보를 관리한다.
- **Metadata Store**: 각 도구의 파라미터 스키마, 타입 정보, 설명(Description)을 저장한다.

### 2.2 Argument Resolver (인자 해석기)
수신된 데이터 뭉치를 실행 가능한 형태의 인자 세트로 정제하는 컴포넌트이다.
- **Type Transformer**: JSON 타입의 데이터를 내부 함수가 요구하는 구체적인 데이터 타입으로 변환한다.
- **Value Injector**: 누락된 필수 인자에 대해 정의된 기본값(Default)을 할당하거나, 환경 변수/상태값으로부터 동적 인자를 주입한다.
- **Key Mapper**: MCP 도구 명세의 키 이름과 실제 함수 인자 명칭 간의 불일치를 해결한다.

### 2.3 Schema Validator (스키마 검증기)
정제된 인자가 실행 가능한 상태인지 검증하는 독립적인 컴포넌트이다.
- **Structural Validator**: 인자의 구성(필수 인자 포함 여부, 개수)이 정의된 스키마와 일치하는지 확인한다.
- **Constraint Checker**: 값의 범위(Range), 패턴(Regex), 값의 유효성(Enum) 등 비즈니스 제약 조건을 검사한다.

### 2.4 Dispatcher (분배기)
검증이 완료된 인자를 최종 실행 대상에게 전달하는 컴포넌트이다.
- **Caller**: 매핑된 함수 객체를 호출하며, 인자를 전달한다.
- **Result Formatter**: 실행 결과(성공/실패/데이터)를 MCP 프로토콜 응답 규격에 맞게 패키징한다.

---

## 3. 컴포넌트 간 상호작용 흐름 (Component Interaction Flow)

1.  **Discovery**: `Registry Manager`가 요청된 도구의 존재 여부와 메타데이터를 제공한다.
2.  **Resolution**: `Argument Resolver`가 원시 데이터를 정제된 인자 세트로 변환한다.
3.  **Verification**: `Schema Validator`가 변환된 인자의 유효성을 최종 확인한다.
4.  **Execution**: `Dispatcher`가 최종 인자를 사용하여 실제 함수를 실행하고 결과를 반환한다.

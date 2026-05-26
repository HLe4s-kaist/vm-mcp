# Virtual Monitor MCP Server

[English Version](README.en.md)

> [!IMPORTANT]
> 해당 레포지토리는 모든 코드를 AI에 의해 구현하였습니다. 모든 책임은 본인에게 있습니다.

## 개요 (Overview)

본 프로젝트는 CLI(Command Line Interface) 환경에서 동작하는 AI 에이전트가 GUI(Graphical User Interface) 중심의 운영체제 환경을 인간 사용자와 유사한 방식으로 상호작용하고 조작할 수 있도록 하는 브릿지를 구축하는 것을 목적으로 합니다.

### 핵심 가치
- **Headless 환경의 시각화**: GUI가 없는 서버 환경이나 가상 머신(VM)에 가상 모니터를 생성하여 시각적 피드백 제공.
- **에이전트 중심 자동화**: AI 에이전트가 스크린을 보고, 마우스를 움직이고, 키보드를 입력하여 GUI 기반 작업을 수행할 수 있는 인터페이스 제공.
- **실시간 모니터링**: 사용자가 웹 브라우저를 통해 에이전트의 동작을 실시간으로 감시할 수 있는 환경 제공.

## Core Features

1.  **Virtual Monitor Creation**: Headless 시스템에 가상 디스플레이(Xvfb)를 생성하여 GUI 환경을 제공합니다.
2.  **GUI Interaction**: PyAutoGUI를 통한 GUI 자동화 기능:
    *   화면 캡처/읽기
    *   마우스 이동, 클릭, 드래그
    *   키보드 입력 (타이핑, 단축키)
3.  **MCP Protocol 지원**: 표준 MCP(Model Context Protocol)를 통해 AI 에이전트가 도구를 호출합니다.
4.  **Web-based Monitoring**: 실시간 웹 뷰어(Port 8080)를 통한 가상 데스크톱 모니터링 및 원격 조작.

## 설치 및 실행 가이드 (Installation & Usage Guide)

### 1. 시스템 패키지 설치
GUI 자동화 및 가상 프레임버퍼 구동을 위해 다음 시스템 패키지가 필요합니다. (Ubuntu/Debian 기준)
```bash
sudo apt-get update
sudo apt-get install -y xvfb xdotool scrot python3-tk python3-dev
```

### 2. 파이썬 의존성 패키지 설치
```bash
pip install pyautogui pillow websockets mcp mss starlette uvicorn pyperclip python-xlib
```

### 3. 프로젝트 실행

#### 로컬 stdio 모드 (기본)
AI 에이전트(예: Claude Desktop)가 로컬에서 직접 프로세스를 실행하여 stdin/stdout으로 통신합니다.
```bash
python3 src/main.py
```

#### 원격 HTTP 모드 (streamable-http)
외부 클라이언트가 네트워크를 통해 접속할 수 있도록 HTTP 서버를 노출합니다.
```bash
python3 src/main.py --mcp-transport streamable-http --mcp-port 8001
```

실행 후:
- 웹 뷰어: `http://localhost:8080` (가상 데스크톱 실시간 모니터링)
- MCP 엔드포인트: `http://localhost:8001/mcp/` (AI 에이전트 연동용)

### 4. 통합 검증 테스트 실행

- **포트 바인딩 및 웹 페이지 로드 테스트**:
  ```bash
  python3 tests/test_run.py
  ```
- **MCP stdio JSON-RPC 프로토콜 규격 및 도구 호출 테스트**:
  ```bash
  python3 tests/test_mcp.py
  ```
- **WebSocket 기반 마우스/키보드 인터랙션 테스트**:
  ```bash
  python3 tests/test_interaction.py
  ```
- **Streamable HTTP 원격 MCP 전송 테스트**:
  ```bash
  python3 tests/test_streamable_http.py
  ```

### 5. 가상 화면에 GUI 프로그램 실행하여 확인하기
가상 디스플레이(Xvfb)는 기본적으로 빈 화면(검은 화면) 상태입니다. 화면에 GUI 창을 띄워 제어해 보려면 다음과 같이 실행합니다.

#### 1) 테스트용 GUI 프로그램 설치
```bash
sudo apt-get install -y x11-apps gedit
```

#### 2) 가상 디스플레이에서 프로그램 실행
```bash
# 눈동자가 마우스를 따라 움직이는 xeyes 데모 실행
./run_app.sh xeyes

# 메모장 프로그램 gedit 실행
./run_app.sh gedit
```

## MCP 클라이언트 연결 가이드 (MCP Client Connection Guide)

### 방법 1: 로컬 stdio 연결 (권장)
로컬 머신에서 실행하거나, AI 에이전트가 직접 프로세스를 시작하는 경우.

#### Claude Desktop 설정 예시
로컬 PC의 Claude Desktop 설정 파일(`claude_desktop_config.json`)에 다음을 추가합니다.

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "virtual-monitor": {
      "command": "python3",
      "args": ["/path/to/vmvm/src/main.py"]
    }
  }
}
```

### 방법 2: 원격 Streamable HTTP 연결
원격 서버(VM 등)에서 실행 중인 MCP 서버에 네트워크를 통해 접속하는 경우.

#### 1) 서버 측: HTTP 모드로 시작
```bash
python3 src/main.py --mcp-transport streamable-http --mcp-port 8001 --mcp-host 0.0.0.0
```

#### 2) 클라이언트 측: Claude Desktop 설정
```json
{
  "mcpServers": {
    "virtual-monitor": {
      "type": "streamable-http",
      "url": "http://<SERVER_IP>:8001/mcp/"
    }
  }
}
```

> `<SERVER_IP>`에 실제 서버의 IP 주소를 입력합니다.

#### 3) Python 클라이언트로 프로그래밍 방식 연동
```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def main():
    url = "http://<SERVER_IP>:8001/mcp/"
    async with streamable_http_client(url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 도구 목록 확인
            tools = await session.list_tools()
            print([t.name for t in tools.tools])
            
            # 스크린 메타데이터 조회
            result = await session.call_tool("get_screen_metadata", {})
            print(result.content[0].text)
            
            # 스크린샷 촬영
            screenshot = await session.call_tool("screenshot", {"format_type": "png"})
            print(f"Screenshot base64 length: {len(screenshot.content[0].text)}")

asyncio.run(main())
```

### 제공되는 MCP 도구 목록

| 도구 이름 | 설명 |
|-----------|------|
| `get_screen_metadata` | 화면 해상도, 디스플레이 상태 등 메타데이터 조회 |
| `screenshot` | 가상 모니터 스크린샷 촬영 (Base64 인코딩) |
| `click` | 지정 좌표에 마우스 클릭 (좌표: 0.0~1.0 정규화) |
| `move_to` | 마우스 커서 이동 |
| `drag_to` | 마우스 드래그 |
| `scroll` | 마우스 휠 스크롤 |
| `type` | 텍스트 입력 (키보드/클립보드 자동 선택) |
| `press` | 단일 키 또는 키 조합 입력 (예: `ctrl+c`) |
| `key_down` | 키 누르고 있기 |
| `key_up` | 눌린 키 해제 |
| `get_config` | 시스템 설정 조회 |
| `set_config` | 시스템 설정 변경 |

### 제공되는 MCP 리소스 목록

| 리소스 URI | 설명 |
|------------|------|
| `screen://current` | 가상 모니터의 실시간 스크린 캡처 (바이너리 PNG 데이터 반환) |

### 네트워크 트러블슈팅

- **방화벽**: 원격 접속 시 포트(기본 8001)가 방화벽에 의해 차단되지 않았는지 확인하세요.
  ```bash
  sudo ufw allow 8001/tcp
  ```
- **바인드 호스트**: 외부 접속을 허용하려면 `--mcp-host 0.0.0.0`을 명시하세요.
- **클라이언트 재시작**: 서버를 재시작한 후에는 클라이언트(Claude Desktop 등)도 반드시 재시작해야 합니다.

## 라이선스 (License)

본 프로젝트는 GPLv2 (GNU General Public License v2.0) 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하십시오.

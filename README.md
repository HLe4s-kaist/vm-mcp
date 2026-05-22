# Virtual Monitor MCP Server

## 개요 (Overview)

본 프로젝트는 CLI(Command Line Interface) 환경에서 동작하는 AI 에이전트가 GUI(Graphical User Interface) 중심의 운영체제 환경을 인간 사용자와 유사한 방식으로 상호작용하고 조작할 수 있도록 하는 브릿지를 구축하는 것을 목적으로 합니다.

### 핵심 가치
- **Headless 환경의 시각화**: GUI가 없는 서버 환경이나 가상 머신(VM)에 가상 모니터를 생성하여 시각적 피드백 제공.
- **에이전트 중심 자동화**: AI 에이전트가 스크린을 보고, 마우스를 움직이고, 키보드를 입력하여 GUI 기반 작업을 수행할 수 있는 인터페이스 제공.
- **실시간 모니터링**: 사용자가 웹 브라우저나 VNC 클라이언트를 통해 에이전트의 동작을 실시간으로 감시할 수 있는 환경 제공.

## Core Features

1.  **Virtual Monitor Creation**: Establish a virtual display on headless systems (e.g., VMware, QEMU) to provide a visual interface for headless environments.
2.  **GUI Interaction**: Provide capabilities similar to `pyautogui`, including:
    *   Screen reading/capturing.
    *   Mouse movements and clicks.
    *   Keyboard input.
3.  **Agent-Driven Automation**: Enable AI agents to autonomously operate a computer to perform GUI-based tasks, such as software development and testing, directly from a CLI environment.
4.  **VNC-based Monitoring**: Support visual monitoring of the virtual monitor's state (screen, mouse, and keyboard inputs) via VNC protocols (e.g., TightVNC).
5.  **Web-based Monitoring Interface**: The MCP server will host a web server to allow users and agents to monitor the virtual desktop in real-time through a browser.

## Goals

The ultimate goal is to bridge the gap between CLI-driven AI agents and GUI-centric software environments, allowing agents to interact with any desktop environment with the same proficiency as a human user.

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
메인 오케스트레이터를 실행하여 가상 모니터(Xvfb `:99`)와 웹 뷰어 서버(Port `8080`) 및 MCP stdio 서버를 동시 구동합니다.
```bash
python3 src/main.py
```
- 실행 후 브라우저에서 `http://localhost:8080`에 접속하면, 미려한 다크 모드 UI의 **VM Monitor Bridge** 웹 뷰어가 나타납니다.
- 웹 뷰어 화면 위에서 마우스 드래그, 클릭, 이동, 마우스 휠 스크롤 조작을 실시간으로 수행하여 가상 환경을 직접 컨트롤할 수 있습니다.
- 키보드로 글자를 타이핑하거나 우측의 특수 핫키 패널을 사용하여 원격으로 키 입력을 보낼 수 있습니다.

### 4. 통합 검증 테스트 실행
시스템이 올바르게 구성되어 구동되는지 검증하기 위한 통합 테스트 스크립트를 제공합니다.

- **포트 바인딩 및 웹 페이지 로드 테스트**:
  ```bash
  python3 tests/test_run.py
  ```
- **MCP stdio JSON-RPC 프로토콜 규격 및 도구 호출 테스트**:
  ```bash
  python3 tests/test_mcp.py
  ```
- **WebSocket 기반 양방향 마우스 드래그/이동/스크롤 이벤트 인터랙션 테스트**:
  ```bash
  python3 tests/test_interaction.py
  ```

### 5. 가상 화면에 GUI 프로그램 실행하여 확인하기
가상 디스플레이(Xvfb)는 기본적으로 빈 화면(검은 화면) 상태입니다. 화면에 GUI 창을 띄워 제어해 보려면 다음과 같이 실행합니다.

#### 1) 테스트용 GUI 프로그램 설치
간단한 데모 프로그램(`xeyes` 등)이나 텍스트 에디터(`gedit`)를 설치합니다.
```bash
sudo apt-get install -y x11-apps gedit
```

#### 2) 가상 디스플레이에서 프로그램 실행
제공되는 `run_app.sh` 헬퍼 스크립트를 사용하여 가상 디스플레이 `:99`에 프로그램을 띄웁니다.
```bash
# 눈동자가 마우스를 따라 움직이는 xeyes 데모 실행
./run_app.sh xeyes

# 메모장 프로그램 gedit 실행
./run_app.sh gedit
```
실행 후 웹 뷰어(`http://localhost:8080`) 화면을 보면 프로그램 창이 정상적으로 표시되며, 마우스로 창을 클릭하거나 드래그하여 조작할 수 있습니다.

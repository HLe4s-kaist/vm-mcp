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

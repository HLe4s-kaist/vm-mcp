FROM ubuntu:24.04

USER root

RUN apt update && apt install -y curl vim wget xz-utils tightvncserver git xvfb xdotool scrot python3-tk python3-dev iproute2 gedit python3.12-venv
RUN curl -fsSL https://antigravity.google/cli/install.sh | bash 
RUN git clone https://github.com/HLe4s-kaist/vm-mcp.git /root/vm-mcp
RUN printf "rootroot\nrootroot\n\n" | vncpasswd
RUN mkdir -p /root/venv
RUN python3 -m venv /root/venv/
RUN echo "source /root/venv/bin/activate" >> /root/.bashrc
RUN /root/venv/bin/pip install pyautogui pillow websockets mcp mss starlette uvicorn pyperclip python-xlib asyncvnc
RUN USER=root vncserver :0 -geometry 1920x1080 -name main

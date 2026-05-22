#!/bin/bash
# 가상 디스플레이 :99 환경에서 지정한 GUI 프로그램을 백그라운드로 실행해주는 헬퍼 스크립트입니다.
# 사용법: ./run_app.sh gedit
#         ./run_app.sh xeyes

if [ -z "$1" ]; then
    echo "사용법: ./run_app.sh [프로그램명]"
    echo "예시: ./run_app.sh xeyes"
    exit 1
fi

# 가상 디스플레이 환경 변수 바인딩
export DISPLAY=:99

# Xauthority 파일 위치 바인딩
if [ -f "$HOME/.Xauthority" ]; then
    export XAUTHORITY=$HOME/.Xauthority
fi

echo "가상 디스플레이 :99 에서 '$*' 프로그램을 실행합니다..."
"$@" &

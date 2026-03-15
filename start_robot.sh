#!/bin/bash
PROJECT_DIR="/home/matija/robot_project"
VENV_DIR="$PROJECT_DIR/venv"
SESSION_NAME="robot"

sleep 5

tmux kill-session -t "$SESSION_NAME" 2>/dev/null

tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_DIR" \
    "source $VENV_DIR/bin/activate && python3 main.py --test; echo ''; echo 'Program se je koncal. Pritisnite Enter za ponovni zagon ali Ctrl+C za izhod.'; read; exec bash"

#!/bin/bash
STREAMLIT="/Library/Frameworks/Python.framework/Versions/3.14/bin/streamlit"
APP_DIR="/Users/qasimt/Desktop/Claude Code 1/expense_tracker"

# If already running on port 8501, just open browser
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    open "http://localhost:8501"
    exit 0
fi

# Start Streamlit in background, log output
cd "$APP_DIR"
"$STREAMLIT" run app.py --server.headless true > /tmp/bm_tracker.log 2>&1 &

# Wait for server to be ready (up to 10s)
for i in $(seq 1 20); do
    if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

open "http://localhost:8501"

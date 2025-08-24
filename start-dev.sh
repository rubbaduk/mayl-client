#!/bin/bash

# gmail ai assistant - development startup script
# automatically starts both fastapi backend and react frontend servers

echo "starting gmail ai assistant development servers..."
echo "=================================================="

# get the script directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "project directory: $PROJECT_DIR"

# function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# function to check if a port is in use
port_in_use() {
    lsof -ti:$1 >/dev/null 2>&1
}

echo ""
echo "checking dependencies..."

# check if required commands exist
if ! command_exists python; then
    echo "error: python not found. please install python 3.8+."
    exit 1
fi

if ! command_exists npm; then
    echo "error: npm not found. please install node.js and npm."
    exit 1
fi

# check python version
PYTHON_VERSION=$(python --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
echo "python $PYTHON_VERSION found"

# check node version
NODE_VERSION=$(node --version 2>/dev/null || echo "not found")
echo "node.js $NODE_VERSION found"

# check if virtual environment exists
if [ -d "$PROJECT_DIR/.venv" ]; then
    echo "virtual environment found"
else
    echo "warning: virtual environment not found at $PROJECT_DIR/.venv"
    echo "   run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

# check if frontend dependencies are installed
if [ -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo "frontend dependencies installed"
else
    echo "warning: frontend dependencies not found"
    echo "   run: cd frontend && npm install"
fi

echo ""
echo "cleaning up existing processes..."

# kill any existing processes on our ports
if port_in_use 8000; then
    echo "stopping existing backend server (port 8000)..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if port_in_use 5173; then
    echo "stopping existing frontend server (port 5173)..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo "ports cleared"

echo ""
echo "starting fastapi backend server..."

# start backend in a new terminal
osascript <<EOF
tell application "Terminal"
    do script "
        echo 'gmail ai assistant - backend server'
        echo '====================================='
        echo 'starting fastapi server on port 8000...'
        echo ''
        cd '$PROJECT_DIR'
        
        # activate virtual environment if it exists
        if [ -f '.venv/bin/activate' ]; then
            echo 'activating virtual environment...'
            source .venv/bin/activate
        fi
        
        echo 'starting uvicorn server...'
        python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
    "
end tell
EOF

echo "backend server starting in new terminal..."

# wait for backend to start
echo "waiting for backend to initialize..."
sleep 4

# check if backend started successfully
if port_in_use 8000; then
    echo "backend server running on port 8000"
else
    echo "warning: backend server may not have started properly"
fi

echo ""
echo "starting react frontend server..."

# start frontend in a new terminal
osascript <<EOF
tell application "Terminal"
    do script "
        echo 'gmail ai assistant - frontend server'
        echo '======================================'
        echo 'starting react development server on port 5173...'
        echo ''
        cd '$PROJECT_DIR/frontend'
        
        # check if node_modules exists
        if [ ! -d 'node_modules' ]; then
            echo 'installing dependencies first...'
            npm install
        fi
        
        echo 'starting vite development server...'
        npm run dev
    "
end tell
EOF

echo "frontend server starting in new terminal..."

# wait for frontend to start
echo "waiting for frontend to initialize..."
sleep 3

echo ""
echo "development servers are starting!"
echo "=================================="
echo ""
echo "server urls:"
echo "   frontend:  http://localhost:5173"
echo "   backend:   http://localhost:8000"
echo "   api docs:  http://localhost:8000/docs"
echo ""
echo "next steps:"
echo "   1. open http://localhost:5173 in your browser"
echo "   2. click 'sign in with google' to test oauth"
echo "   3. check both terminal windows for server logs"
echo ""
echo "to stop servers:"
echo "   - close the terminal windows, or"
echo "   - press ctrl+c in each terminal"
echo ""
echo "troubleshooting:"
echo "   - backend issues: check the fastapi terminal for errors"
echo "   - frontend issues: check the vite terminal for errors"
echo "   - import errors: make sure .venv is activated and dependencies installed"
echo ""

# function to check server health
check_servers() {
    echo "checking server health..."
    
    # check backend
    if curl -s http://localhost:8000/docs >/dev/null 2>&1; then
        echo "backend: healthy (fastapi docs accessible)"
    else
        echo "backend: not responding"
    fi
    
    # check frontend
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        echo "frontend: healthy (vite server responding)"
    else
        echo "frontend: not responding"
    fi
}

# wait a bit more then check health
echo "final health check in 5 seconds..."
sleep 5
check_servers

echo ""
echo "development environment ready!"
echo "press ctrl+c to exit this script (servers will continue running)"
echo ""

# keep script running so you can see status
trap 'echo ""; echo "script exiting. servers are still running in their terminals."; exit 0' INT

# show live status updates
while true; do
    sleep 30
    echo "$(date '+%H:%M:%S') - servers still running..."
done
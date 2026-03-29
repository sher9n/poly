#!/bin/bash
# Start both backend and frontend

echo "Starting PolyTrader..."

# Start backend
echo "Starting backend on :8000..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting frontend on :3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "PolyTrader is running!"
echo "  Dashboard: http://localhost:3000"
echo "  API:       http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop..."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

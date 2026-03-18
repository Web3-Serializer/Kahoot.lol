@echo off
echo [*] Installing frontend dependencies...
call npm install
echo [*] Starting frontend on http://localhost:3000
call npm run dev

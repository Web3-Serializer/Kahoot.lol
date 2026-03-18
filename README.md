<div align="center">

# ⚡ kahoot.lol

**Reverse-engineered Kahoot game bot with a full-stack dashboard.**

Automated session handshake, multi-bot lobbying, AI-powered answer finding, reaction flooding, 2FA support, and more.

[![Python](https://img.shields.io/badge/python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Tailwind](https://img.shields.io/badge/Tailwind-38B2AC?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com)

</div>

---

## How It Works

The Kahoot session handshake was fully reverse-engineered from the browser WebSocket traffic:

```
1. GET /reserve/session/<pin>  →  x-kahoot-session-token header + challenge JS
2. Eval challenge JS           →  XOR mask (decode cipher with arithmetic offset)
3. XOR(base64_decode(header), mask)  →  final WSS token
4. Connect wss://kahoot.it/cometd/<pin>/<token>
5. CometD Bayeux handshake + login + subscribe
6. Listen for game events, answer questions, send reactions
```

The challenge JS contains Unicode whitespace characters (U+2003 etc.) as anti-bot measures. These are stripped before evaluation.

---

## Features

### 🎮 Play Modes
| Mode | Description |
|------|-------------|
| **Random** | Random answers for each question |
| **AI** | Uses Ollama to guess quiz title, searches Kahoot API, auto-answers correctly |
| **Always First** | Always picks choice 0 |
| **Always Last** | Always picks the last choice |
| **Spectator** | Joins the lobby without answering |

### 🧠 AI Mode (Ollama)
*- this may be broken, i am so bored to fix theses*

When AI mode is selected, the bot uses a local LLM to find the quiz:

```
START_QUIZ event received (Q1 text + answer choices)
         │
         ▼
  Ollama guesses the quiz TITLE from Q1 data
  (e.g. Q1: "A noun is..." → guesses: "English A1", "Grammar Quiz", ...)
         │
         ▼
  Each guessed title is searched on Kahoot's public API
  (https://create.kahoot.it/rest/kahoots/?query=...)
         │
         ▼
  Results are verified by matching quizQuestionAnswers
  (number of choices per question must match exactly)
         │
         ▼
  ✓ Found → all correct answers cached, 100% accuracy
  ✗ Not found → Q1 from game data + random for rest
```

### 🤖 Multi-Bot
- Launch 1-50 bots per session
- Custom naming: themes (hacker, animal, space, meme), prefix, or fully custom names
- Configurable join delay between bots
- Auto-reconnect on crash

### 💬 Reactions
- **Flood**: spam reactions continuously with configurable speed (ms)
- **React on Win**: send a reaction when answering correctly
- **React on Lose**: send a reaction when answering wrong
- **Celebrate**: spam reactions when the game ends
- All reactions support **🎲 Random** mode (picks a random emoji each time)
- Available reactions: 👍 👏 😂 🤔 😮 ❤️

### 🔐 2FA Support
- When the host enables two-step join, the dashboard shows 4 color buttons (🔴🔵🟡🟢)
- Enter the sequence shown on the host screen and submit
- All bots receive the 2FA code simultaneously

### ⚙️ Advanced
- Answer delay (min/max ms) to simulate human response time
- Join delay between bots
- Per-bot scoreboard with score, rank, streak, W/L ratio
- Live color-coded logs with timestamps
- Credit system with admin panel

### 👤 User System
- Token-based authentication (no password, no email)
- Credit system: 1 credit per bot per session
- Admin panel to manage users, add/remove credits, promote, delete

---

## Quick Start

### Prerequisites
- **Python 3.9+**
- **Node.js 18+**
- **Ollama** (optional, for AI mode): [ollama.com](https://ollama.com)

### Windows

```bash
# Extract the project
# Double-click start.bat
# OR manually:

# Terminal 1 (Backend)
cd backend
pip install -r requirements.txt
mkdir data
uvicorn app.main:app --reload --port 8000

# Terminal 2 (Frontend)
cd frontend
npm install
npm run dev

# Terminal 3 (Create admin, once)
curl -X POST http://localhost:8000/api/admin/init
```

Open **http://localhost:5173** and login with the admin token from the curl response.

### Docker

```bash
docker compose up --build
curl -X POST http://localhost:8000/api/admin/init
```

Open **http://localhost:3000**

### Ollama (optional)

```bash
# Install from https://ollama.com/download
ollama pull llama3.2
# That's it, the dashboard auto-detects it
```

---

## Project Structure

```
kahoot-dashboard/
├── docker-compose.yml
├── start.bat                    # Windows one-click launcher
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes
│   │   ├── auth.py              # JWT authentication
│   │   └── database.py          # SQLAlchemy models (SQLite)
│   ├── libs/
│   │   ├── __init__.py          # KahootBot reverse-engineered wrapper
│   │   ├── manager.py           # Multi-bot orchestration
│   │   └── ollama.py            # Local LLM integration
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── LoginPage.tsx     # Token auth UI
    │   │   ├── DashboardPage.tsx # Main control panel
    │   │   └── AdminPage.tsx     # User management
    │   ├── hooks/useAuth.tsx     # Auth context
    │   ├── lib/api.ts            # API client
    │   └── App.tsx               # Router
    ├── tailwind.config.js
    └── Dockerfile
```

---

## API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account, returns access token |
| POST | `/api/auth/login` | Login with token, returns JWT |
| GET | `/api/user/me` | Current user info |

### Game
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/game/start` | Start a bot session |
| POST | `/api/game/{id}/stop` | Stop a session |
| GET | `/api/game/{id}/status` | Live status + logs + bot scoreboard |
| POST | `/api/game/{id}/2fa` | Submit 2FA color sequence |
| GET | `/api/game/sessions` | List past sessions |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/init` | Create first admin account |
| GET | `/api/admin/users` | List all users |
| POST | `/api/admin/credits/add` | Add/remove credits |
| POST | `/api/admin/delete` | Delete user |
| POST | `/api/admin/promote` | Promote to admin |

### Ollama
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ollama/status` | Check Ollama connection + list models |

---

## Game Config Options

```json
{
  "pin": "123456",
  "bot_count": 5,
  "mode": "ai",
  "spectator": false,
  "name_mode": "theme",
  "name_theme": "hacker",
  "name_prefix": "Bot",
  "custom_names": ["Alice", "Bob"],
  "answer_delay_min": 500,
  "answer_delay_max": 2000,
  "join_delay": 500,
  "flood_react": true,
  "flood_reaction": "random",
  "flood_speed": 500,
  "react_on_win": true,
  "win_reaction": "random",
  "react_on_lose": true,
  "lose_reaction": "thinking",
  "celebrate": true,
  "celebrate_reaction": "heart",
  "celebrate_count": 10,
  "auto_reconnect": true,
  "ollama_model": "llama3.2"
}
```

---

## Reverse Engineering Notes

### Session Handshake
The challenge JS returned by `/reserve/session/` contains an obfuscated decode function with an arithmetic offset expression. Kahoot injects Unicode whitespace (U+2003 em-space, etc.) into the expression as anti-bot measures. The offset is evaluated using a safe AST walker, and the decode cipher runs `((charCode * position + offset) % 77) + 48` on each character. The result is XOR'd with the base64-decoded session token header to produce the WebSocket connection token.

### CometD Protocol
The WebSocket uses CometD (Bayeux) protocol. The exact message sequence matters: the browser sends two `/meta/connect` messages before login, with specific `advice` and `ack` values. The login content must be `"{}"` (empty JSON string), and a second controller message with `{"usingNamerator": false}` must follow.

### Received Events
| ID | Event | Description |
|----|-------|-------------|
| 1 | GET_READY | Countdown before question |
| 2 | START_QUESTION | Question is live |
| 3 | GAME_OVER | Game ended |
| 8 | REVEAL_ANSWER | Answer results (score, rank, streak) |
| 9 | START_QUIZ | Quiz started (Q1 data + quizQuestionAnswers) |
| 14 | USERNAME_ACCEPTED | Player name confirmed |
| 17 | RECOVERY_DATA | Game state (gameApiId, avatar, etc.) |
| 51 | 2FA_INCORRECT | Wrong 2FA code |
| 52 | 2FA_CORRECT | 2FA accepted |
| 53 | RESET_2FA | 2FA required |

### Sent Messages
| ID | Action | Description |
|----|--------|-------------|
| 16 | INIT | Send `{"usingNamerator": false}` after login |
| 45 | ANSWER | Submit answer `{"type": "quiz", "choice": N, "questionIndex": N}` |
| 47 | REACTION | Send reaction `{"reactionType": "ThumbsUp"}` |
| 50 | SUBMIT_2FA | Submit 2FA sequence `{"gameId": pin, "sequence": [0,1,2,3]}` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy, websocket-client |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| AI | Ollama (local LLM) |
| Database | SQLite |
| Auth | JWT (python-jose) |
| Deploy | Docker Compose |

---

## Disclaimer

This project is for **educational and research purposes only**. It demonstrates WebSocket reverse engineering, CometD protocol analysis, and full-stack development. Use responsibly. (annoying teachers is authorized 🦉)

---

<div align="center">
  <sub>Built by reverse-engineering Kahoot's WebSocket handshake from scratch.</sub>
</div>

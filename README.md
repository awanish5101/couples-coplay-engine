# Couples Co-Play & Game Personalization Engine

[![CI](https://github.com/awanish5101/couples-coplay-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/awanish5101/couples-coplay-engine/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Real-time synchronized bedtime co-play engine and AI game personalization platform designed for couples. Enables low-latency synchronous multiplayer game loops, dual-blind answer submissions, simultaneous reveals, and automated dynamic game generation synthesized on the spot from couple interests, relationship milestones, and banter styles.

---

## Key Features

- **AI Game Personalization Engine:**
  - Dynamically synthesizes daily bedtime games (This or That, Deep Talk, Trivia, Rapid Fire, Co-op Story) personalized to couple interests, relationship length, and humor styles.
  - Strict Pydantic schema validation with deterministic fallback generators ensuring sub-50ms synthesis and zero downtime.
- **Synchronous Real-Time Co-Play (WebSockets):**
  - Room coordination pairing partners using 6-character room codes.
  - State machine: `WAITING_FOR_PARTNER` -> `ROUND_ACTIVE` -> `WAITING_FOR_REVEAL` -> `ROUND_RECAP` -> `GAME_COMPLETE`.
  - **Dual-Blind Reveal Mechanics:** Answers are masked until both partners submit, triggering an instant synchronized reveal with compatibility scoring and conversation follow-ups.
  - Heartbeat ping/pong, graceful partner disconnect alerts, and session state recovery.
- **Production Architecture & Testing:**
  - FastAPI async event loop with full CORS middleware.
  - Automated test coverage across AI generation, room orchestration, and WebSocket streaming (100% test pass rate).
  - Dockerized with `docker-compose` support and GitHub Actions CI.

---

## System Architecture

```text
  Mobile / Web Client (Partner A)           Mobile / Web Client (Partner B)
              │                                         │
              ├── WebSocket (ws://) ─────────────── WebSocket (ws://)
              │                                         │
              ▼                                         ▼
      ┌────────────────────────────────────────────────────────┐
      │             FastAPI Co-Play Orchestrator               │
      │  ┌────────────────────────┐  ┌──────────────────────┐  │
      │  │      Room Manager      │  │  AI Personalization  │  │
      │  │  (State Machine & Sync)│  │ (Dynamic Synthesizer)│  │
      │  └────────────────────────┘  └──────────────────────┘  │
      └────────────────────────────────────────────────────────┘
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
            Redis Session Store      PostgreSQL History
```

---

## Quickstart

### 1. Local Setup

```bash
git clone https://github.com/awanish5101/couples-coplay-engine.git
cd couples-coplay-engine

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run test suite
pytest tests -v

# Start local dev server
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation available at `http://localhost:8000/docs`.

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

---

## API Specification

### REST Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness probe and active session metrics |
| `POST` | `/api/sessions/create` | Create a co-play room from couple profile |
| `POST` | `/api/sessions/join` | Partner joins session via 6-digit room code |
| `GET` | `/api/sessions/{session_id}` | Fetch current session state & active question |
| `POST` | `/api/sessions/{session_id}/answer` | Submit answer for current round |
| `POST` | `/api/sessions/{session_id}/next` | Advance room to next round |

### WebSocket Endpoint

```text
WS /ws/{session_id}/{player_id}
```

* **Client Events:** `PING`, `SUBMIT_ANSWER`
* **Server Events:** `PLAYER_CONNECTED`, `PARTNER_JOINED`, `PARTNER_SUBMITTED`, `ROUND_REVEAL`, `ROUND_ADVANCED`, `PARTNER_DISCONNECTED`

---

## License

MIT License. Developed by [Awanish Chaurasiya](https://github.com/awanish5101).

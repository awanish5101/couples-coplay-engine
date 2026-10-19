import json
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models import CoupleProfile, SessionState, SessionStatus, RevealPayload
from app.room_manager import RoomManager

app = FastAPI(
    title="Couples Co-Play & Personalization Engine",
    description="Real-time synchronized bedtime co-play engine with AI game personalization for couples",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

room_manager = RoomManager()


class ConnectionManager:
    """Manages active WebSockets and coordinates real-time broadcasts per room."""
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, session_id: str, player_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        self.active_connections[session_id][player_id] = websocket

    def disconnect(self, session_id: str, player_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(player_id, None)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_to_room(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for pid, ws in list(self.active_connections[session_id].items()):
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    async def send_personal(self, session_id: str, player_id: str, message: dict):
        if session_id in self.active_connections and player_id in self.active_connections[session_id]:
            try:
                await self.active_connections[session_id][player_id].send_json(message)
            except Exception:
                pass


ws_manager = ConnectionManager()


class JoinRoomRequest(BaseModel):
    room_code: str
    partner_id: str
    partner_name: str


class AnswerSubmissionRequest(BaseModel):
    player_id: str
    round_index: int
    answer: str


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "active_sessions": len(room_manager.sessions),
        "service": "couples-coplay-engine"
    }


@app.post("/api/sessions/create", response_model=SessionState)
def create_game_session(profile: CoupleProfile):
    session = room_manager.create_session(profile)
    return session


@app.post("/api/sessions/join", response_model=SessionState)
async def join_room(payload: JoinRoomRequest):
    session = room_manager.join_by_code(payload.room_code, payload.partner_id, payload.partner_name)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with code {payload.room_code} not found."
        )

    await ws_manager.broadcast_to_room(
        session.session_id,
        {
            "event": "PARTNER_JOINED",
            "partner_name": payload.partner_name,
            "status": session.status.value,
            "current_round": session.current_round
        }
    )
    return session


@app.get("/api/sessions/{session_id}", response_model=SessionState)
def get_session_state(session_id: str):
    session = room_manager.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/sessions/{session_id}/answer")
async def submit_answer(session_id: str, payload: AnswerSubmissionRequest):
    success, reveal = room_manager.submit_answer(
        session_id=session_id,
        player_id=payload.player_id,
        round_index=payload.round_index,
        answer=payload.answer
    )

    if not success:
        raise HTTPException(status_code=400, detail="Invalid submission or round state")

    session = room_manager.sessions[session_id]

    if reveal is not None:
        # Both submitted: Broadcast simultaneous reveal
        await ws_manager.broadcast_to_room(
            session_id,
            {
                "event": "ROUND_REVEAL",
                "reveal": reveal.model_dump(),
                "status": session.status.value
            }
        )
        return {"status": "REVEALED", "reveal": reveal}
    else:
        # Partner waiting
        await ws_manager.broadcast_to_room(
            session_id,
            {
                "event": "PARTNER_SUBMITTED",
                "player_id": payload.player_id,
                "status": session.status.value
            }
        )
        return {"status": "WAITING_FOR_PARTNER"}


@app.post("/api/sessions/{session_id}/next")
async def next_round(session_id: str):
    success, new_status, new_round = room_manager.advance_to_next_round(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    session = room_manager.sessions[session_id]
    await ws_manager.broadcast_to_room(
        session_id,
        {
            "event": "ROUND_ADVANCED",
            "current_round": new_round,
            "status": new_status.value
        }
    )
    return {"status": new_status.value, "current_round": new_round}


@app.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str):
    await ws_manager.connect(session_id, player_id, websocket)
    try:
        # Notify room of connection
        await ws_manager.broadcast_to_room(
            session_id,
            {
                "event": "PLAYER_CONNECTED",
                "player_id": player_id
            }
        )
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                if action == "PING":
                    await websocket.send_json({"event": "PONG"})
                elif action == "SUBMIT_ANSWER":
                    round_idx = msg.get("round_index", 0)
                    answer = msg.get("answer", "")
                    success, reveal = room_manager.submit_answer(session_id, player_id, round_idx, answer)
                    if reveal:
                        await ws_manager.broadcast_to_room(
                            session_id,
                            {
                                "event": "ROUND_REVEAL",
                                "reveal": reveal.model_dump(),
                                "status": room_manager.sessions[session_id].status.value
                            }
                        )
                    else:
                        await ws_manager.broadcast_to_room(
                            session_id,
                            {
                                "event": "PARTNER_SUBMITTED",
                                "player_id": player_id,
                                "status": room_manager.sessions[session_id].status.value
                            }
                        )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, player_id)
        await ws_manager.broadcast_to_room(
            session_id,
            {
                "event": "PARTNER_DISCONNECTED",
                "player_id": player_id
            }
        )

import random
import string
import uuid
from typing import Dict, Optional, Tuple, Any
from app.models import (
    SessionState,
    SessionStatus,
    GamePackage,
    RevealPayload,
    CoupleProfile
)
from app.ai_engine import PersonalizationEngine


class RoomManager:
    """
    Manages active multiplayer co-play sessions, room codes,
    WebSocket connections, dual-submission reveals, and state synchronization.
    """

    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        self.code_to_session: Dict[str, str] = {}
        self.player_session_index: Dict[str, str] = {}
        self.ai_engine = PersonalizationEngine()

    def generate_room_code(self, length: int = 6) -> str:
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choices(chars, k=length))
            if code not in self.code_to_session:
                return code

    def create_session(self, profile: CoupleProfile) -> SessionState:
        session_id = f"sess-{uuid.uuid4().hex[:10]}"
        room_code = self.generate_room_code()
        game_package = self.ai_engine.generate_daily_game(profile)

        session = SessionState(
            session_id=session_id,
            room_code=room_code,
            couple_id=profile.couple_id,
            status=SessionStatus.WAITING_FOR_PARTNER,
            current_round=0,
            total_rounds=len(game_package.questions),
            game_package=game_package,
            player_names={profile.partner_a_id: profile.partner_a_name}
        )

        self.sessions[session_id] = session
        self.code_to_session[room_code] = session_id
        self.player_session_index[profile.partner_a_id] = session_id
        return session

    def join_by_code(self, room_code: str, partner_id: str, partner_name: str) -> Optional[SessionState]:
        session_id = self.code_to_session.get(room_code.upper())
        if not session_id:
            return None

        session = self.sessions.get(session_id)
        if not session:
            return None

        session.player_names[partner_id] = partner_name
        self.player_session_index[partner_id] = session_id

        # If both players joined, transition to READY / ROUND_ACTIVE
        if len(session.player_names) >= 2 and session.status == SessionStatus.WAITING_FOR_PARTNER:
            session.status = SessionStatus.ROUND_ACTIVE
            session.current_round = 0

        return session

    def submit_answer(self, session_id: str, player_id: str, round_index: int, answer: str) -> Tuple[bool, Optional[RevealPayload]]:
        session = self.sessions.get(session_id)
        if not session:
            return False, None

        if session.status != SessionStatus.ROUND_ACTIVE and session.status != SessionStatus.WAITING_FOR_REVEAL:
            return False, None

        if round_index != session.current_round:
            return False, None

        if round_index not in session.player_submissions:
            session.player_submissions[round_index] = {}

        session.player_submissions[round_index][player_id] = answer

        # Check if both players have submitted
        submitted_players = session.player_submissions[round_index]
        all_players = list(session.player_names.keys())

        if len(submitted_players) < len(all_players):
            session.status = SessionStatus.WAITING_FOR_REVEAL
            return True, None

        # Both players submitted: trigger simultaneous dual reveal
        current_question = session.game_package.questions[round_index]
        answers_dict = {
            session.player_names.get(pid, pid): ans
            for pid, ans in submitted_players.items()
        }

        # Match calculation
        answers_list = list(submitted_players.values())
        is_match = None
        if len(answers_list) >= 2:
            is_match = (answers_list[0].strip().lower() == answers_list[1].strip().lower())

        reveal = RevealPayload(
            round_index=round_index,
            question=current_question,
            answers=answers_dict,
            is_match=is_match,
            compatibility_score=100 if is_match else 50,
            conversation_starter=current_question.follow_up_prompt or "What made you pick that answer?"
        )

        session.status = SessionStatus.ROUND_RECAP
        return True, reveal

    def advance_to_next_round(self, session_id: str) -> Tuple[bool, SessionStatus, int]:
        session = self.sessions.get(session_id)
        if not session:
            return False, SessionStatus.GAME_COMPLETE, 0

        if session.current_round + 1 < session.total_rounds:
            session.current_round += 1
            session.status = SessionStatus.ROUND_ACTIVE
        else:
            session.status = SessionStatus.GAME_COMPLETE

        return True, session.status, session.current_round

    def get_session_by_player(self, player_id: str) -> Optional[SessionState]:
        session_id = self.player_session_index.get(player_id)
        if session_id:
            return self.sessions.get(session_id)
        return None

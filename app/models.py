from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time


class GameCategory(str, Enum):
    TRIVIA = "TRIVIA"
    DEEP_TALK = "DEEP_TALK"
    RAPID_FIRE = "RAPID_FIRE"
    THIS_OR_THAT = "THIS_OR_THAT"
    COOP_STORY = "COOP_STORY"


class SessionStatus(str, Enum):
    WAITING_FOR_PARTNER = "WAITING_FOR_PARTNER"
    READY = "READY"
    ROUND_ACTIVE = "ROUND_ACTIVE"
    WAITING_FOR_REVEAL = "WAITING_FOR_REVEAL"
    ROUND_RECAP = "ROUND_RECAP"
    GAME_COMPLETE = "GAME_COMPLETE"


class AnswerType(str, Enum):
    CHOICE = "CHOICE"
    FREE_TEXT = "FREE_TEXT"
    SLIDER = "SLIDER"


class QuestionItem(BaseModel):
    id: str
    prompt: str
    category: GameCategory
    answer_type: AnswerType = AnswerType.CHOICE
    options: Optional[List[str]] = None
    follow_up_prompt: Optional[str] = None


class GamePackage(BaseModel):
    game_id: str
    title: str
    tagline: str
    category: GameCategory
    questions: List[QuestionItem]
    estimated_minutes: int = 5


class CoupleProfile(BaseModel):
    couple_id: str
    partner_a_id: str
    partner_a_name: str
    partner_b_id: Optional[str] = None
    partner_b_name: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    relationship_length_months: int = 12
    vibe: str = "playful"
    preferred_category: Optional[GameCategory] = None


class SubmissionEvent(BaseModel):
    player_id: str
    round_index: int
    answer: str
    timestamp: float = Field(default_factory=time.time)


class RevealPayload(BaseModel):
    round_index: int
    question: QuestionItem
    answers: Dict[str, str]
    is_match: Optional[bool] = None
    compatibility_score: Optional[int] = None
    conversation_starter: str


class SessionState(BaseModel):
    session_id: str
    room_code: str
    couple_id: str
    status: SessionStatus
    current_round: int = 0
    total_rounds: int
    game_package: GamePackage
    player_sockets: Dict[str, str] = Field(default_factory=dict)
    player_names: Dict[str, str] = Field(default_factory=dict)
    player_submissions: Dict[int, Dict[str, str]] = Field(default_factory=dict)
    scores: Dict[str, int] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

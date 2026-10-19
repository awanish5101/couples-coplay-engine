import pytest
from app.models import CoupleProfile, SessionStatus
from app.room_manager import RoomManager


def test_room_lifecycle_and_dual_reveal():
    manager = RoomManager()
    profile = CoupleProfile(
        couple_id="c-789",
        partner_a_id="user-1",
        partner_a_name="Kabir",
        partner_b_id="user-2",
        partner_b_name="Meera"
    )

    # 1. Host creates room
    session = manager.create_session(profile)
    assert session.status == SessionStatus.WAITING_FOR_PARTNER
    assert len(session.room_code) == 6
    room_code = session.room_code

    # 2. Partner joins with room code
    joined = manager.join_by_code(room_code, "user-2", "Meera")
    assert joined is not None
    assert joined.status == SessionStatus.ROUND_ACTIVE
    assert "user-1" in joined.player_names
    assert "user-2" in joined.player_names

    # 3. User 1 submits answer
    success_1, reveal_1 = manager.submit_answer(
        session_id=session.session_id,
        player_id="user-1",
        round_index=0,
        answer="Midnight Maggi"
    )
    assert success_1 is True
    assert reveal_1 is None  # Waiting for partner
    assert joined.status == SessionStatus.WAITING_FOR_REVEAL

    # 4. User 2 submits same answer -> triggers simultaneous reveal
    success_2, reveal_2 = manager.submit_answer(
        session_id=session.session_id,
        player_id="user-2",
        round_index=0,
        answer="Midnight Maggi"
    )
    assert success_2 is True
    assert reveal_2 is not None
    assert reveal_2.is_match is True
    assert reveal_2.compatibility_score == 100
    assert "Kabir" in reveal_2.answers
    assert "Meera" in reveal_2.answers
    assert joined.status == SessionStatus.ROUND_RECAP

    # 5. Advance round
    adv_ok, status, round_idx = manager.advance_to_next_round(session.session_id)
    assert adv_ok is True
    assert round_idx == 1
    assert status == SessionStatus.ROUND_ACTIVE

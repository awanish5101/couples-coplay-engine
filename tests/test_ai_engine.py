import pytest
from app.models import CoupleProfile, GameCategory
from app.ai_engine import PersonalizationEngine


def test_ai_engine_generates_game_package():
    engine = PersonalizationEngine()
    profile = CoupleProfile(
        couple_id="c-123",
        partner_a_id="p-1",
        partner_a_name="Aarav",
        partner_b_id="p-2",
        partner_b_name="Diya",
        interests=["Indie Music", "Coffee"],
        relationship_length_months=18
    )

    package = engine.generate_daily_game(profile)

    assert package.game_id.startswith("game-")
    assert len(package.questions) > 0
    assert "Aarav" in package.tagline
    assert "Diya" in package.tagline


def test_ai_engine_substitutes_partner_names():
    engine = PersonalizationEngine()
    profile = CoupleProfile(
        couple_id="c-456",
        partner_a_id="p-a",
        partner_a_name="Rohan",
        partner_b_id="p-b",
        partner_b_name="Ananya",
        preferred_category=GameCategory.TRIVIA
    )

    package = engine.generate_daily_game(profile, force_category=GameCategory.TRIVIA)
    assert package.category == GameCategory.TRIVIA

    # Verify Partner A / Partner B are replaced with actual names
    first_q_options = package.questions[0].options
    assert "Rohan" in first_q_options
    assert "Ananya" in first_q_options

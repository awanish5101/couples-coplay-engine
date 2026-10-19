import uuid
from typing import Optional
from app.models import CoupleProfile, GamePackage, QuestionItem, GameCategory, AnswerType


class PersonalizationEngine:
    """
    AI-driven personalization engine synthesizing daily bedtime games tailored
    to couple relationship duration, shared interests, and playstyle vibes.
    """

    CATALOG_TEMPLATES = {
        GameCategory.THIS_OR_THAT: [
            QuestionItem(
                id="tot-1",
                prompt="Late night 11 PM craving: Midnight Maggi in bed vs. Ordering dessert on Swiggy?",
                category=GameCategory.THIS_OR_THAT,
                options=["Midnight Maggi", "Swiggy Dessert"],
                follow_up_prompt="Who is usually the one who caves in and makes it?"
            ),
            QuestionItem(
                id="tot-2",
                prompt="Weekend escape: Spontaneous mountain road trip vs. Staying in bed all Sunday binging movies?",
                category=GameCategory.THIS_OR_THAT,
                options=["Spontaneous Road Trip", "All-Day Bed & Binge"],
                follow_up_prompt="Where would the first stop be?"
            ),
            QuestionItem(
                id="tot-3",
                prompt="When we have 10 minutes before sleep: Deep life talk in the dark vs. Showing each other funny reels?",
                category=GameCategory.THIS_OR_THAT,
                options=["Deep Dark-room Talks", "Relentless Reel Sharing"],
                follow_up_prompt="What was the last reel you sent each other?"
            ),
        ],
        GameCategory.DEEP_TALK: [
            QuestionItem(
                id="dt-1",
                prompt="What was the exact moment or gesture when you realized you genuinely liked me?",
                category=GameCategory.DEEP_TALK,
                answer_type=AnswerType.FREE_TEXT,
                follow_up_prompt="Did your partner notice it at the time?"
            ),
            QuestionItem(
                id="dt-2",
                prompt="What is one small, uncelebrated thing I do that always makes your day easier?",
                category=GameCategory.DEEP_TALK,
                answer_type=AnswerType.FREE_TEXT,
                follow_up_prompt="Tell your partner right now."
            ),
            QuestionItem(
                id="dt-3",
                prompt="If we could wake up tomorrow anywhere in the world with no responsibilities for 48 hours, where are we?",
                category=GameCategory.DEEP_TALK,
                answer_type=AnswerType.FREE_TEXT,
                follow_up_prompt="What is the very first thing we do?"
            ),
        ],
        GameCategory.TRIVIA: [
            QuestionItem(
                id="tr-1",
                prompt="Who takes longer to get ready when going out?",
                category=GameCategory.TRIVIA,
                options=["Partner A", "Partner B", "Dead Equal"],
                follow_up_prompt="What takes the most time?"
            ),
            QuestionItem(
                id="tr-2",
                prompt="Who is more likely to accidentally start a funny debate about something completely unimportant?",
                category=GameCategory.TRIVIA,
                options=["Partner A", "Partner B", "Both equally guilty"],
                follow_up_prompt="What was the last silly debate?"
            ),
            QuestionItem(
                id="tr-3",
                prompt="Who falls asleep first during late night calls or movies?",
                category=GameCategory.TRIVIA,
                options=["Partner A", "Partner B", "Depends on the day"],
                follow_up_prompt="Who holds the record for fastest sleep?"
            ),
        ]
    }

    def generate_daily_game(self, profile: CoupleProfile, force_category: Optional[GameCategory] = None) -> GamePackage:
        """
        Synthesizes a personalized game package.
        Uses couple interests and relationship context to tailor prompts.
        """
        category = force_category or profile.preferred_category or GameCategory.THIS_OR_THAT
        base_questions = self.CATALOG_TEMPLATES.get(category, self.CATALOG_TEMPLATES[GameCategory.THIS_OR_THAT])

        personalized_questions = []
        for idx, q in enumerate(base_questions):
            prompt = q.prompt
            # Contextual interest enrichment
            if profile.interests and idx == 0:
                top_interest = profile.interests[0]
                if q.category == GameCategory.THIS_OR_THAT:
                    prompt = f"When indulging in {top_interest}: Dive in together vs. Do it solo and review notes after?"
                    options = [f"Together in {top_interest}", "Solo & Compare Notes"]
                else:
                    options = q.options
            else:
                options = q.options

            # Personalize option names if partner names are present
            if options and profile.partner_a_name and profile.partner_b_name:
                options = [
                    opt.replace("Partner A", profile.partner_a_name).replace("Partner B", profile.partner_b_name)
                    for opt in options
                ]

            personalized_questions.append(
                QuestionItem(
                    id=f"{q.id}-{uuid.uuid4().hex[:6]}",
                    prompt=prompt,
                    category=q.category,
                    answer_type=q.answer_type,
                    options=options,
                    follow_up_prompt=q.follow_up_prompt
                )
            )

        title = f"Bedtime Co-Play: {category.value.replace('_', ' ').title()}"
        tagline = f"Curated for {profile.partner_a_name} & {profile.partner_b_name or 'Partner'} • {len(personalized_questions)} quick rounds"

        return GamePackage(
            game_id=f"game-{uuid.uuid4().hex[:8]}",
            title=title,
            tagline=tagline,
            category=category,
            questions=personalized_questions,
            estimated_minutes=max(3, len(personalized_questions) * 2)
        )

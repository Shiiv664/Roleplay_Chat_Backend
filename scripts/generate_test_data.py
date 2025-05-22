"""Generate sample data for the application.

This script creates sample data for development and testing purposes.
It populates the database with example characters, user profiles, AI models,
system prompts, chat sessions, and messages.
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add the parent directory to sys.path to allow imports from the app package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Now import all the app modules
from sqlalchemy.orm import Session

from app.models.ai_model import AIModel
from app.models.application_settings import ApplicationSettings
from app.models.character import Character
from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole
from app.models.system_prompt import SystemPrompt
from app.models.user_profile import UserProfile
from app.utils.db import session_scope


def create_sample_characters(session: Session) -> List[Character]:
    """Create sample characters.

    Args:
        session: SQLAlchemy session

    Returns:
        List of created character instances
    """
    characters = [
        Character(
            label="sherlock_holmes",
            name="Sherlock Holmes",
            description=(
                "The world's only consulting detective, known for his logical "
                "reasoning and observational skills."
            ),
        ),
        Character(
            label="eliza",
            name="ELIZA",
            description=(
                "A classic AI therapist from the 1960s, designed to simulate "
                "a psychotherapist."
            ),
        ),
        Character(
            label="hal_9000",
            name="HAL 9000",
            description="The sentient computer from 2001: A Space Odyssey.",
        ),
        Character(
            label="hermione_granger",
            name="Hermione Granger",
            description=(
                "Brilliant witch from the Harry Potter series, known for her "
                "intelligence and logical thinking."
            ),
        ),
        Character(
            label="yoda",
            name="Master Yoda",
            description=(
                "Wise Jedi Master from Star Wars, known for his unique way of "
                "speaking and deep wisdom."
            ),
        ),
    ]

    for character in characters:
        session.add(character)

    session.flush()
    return characters


def create_sample_user_profiles(session: Session) -> List[UserProfile]:
    """Create sample user profiles.

    Args:
        session: SQLAlchemy session

    Returns:
        List of created user profile instances
    """
    user_profiles = [
        UserProfile(
            label="default_user",
            name="Default User",
            description="Default user profile for casual conversations.",
        ),
        UserProfile(
            label="detective",
            name="Detective",
            description="A detective persona for solving mysteries.",
        ),
        UserProfile(
            label="student",
            name="Student",
            description="A student persona for learning and asking questions.",
        ),
    ]

    for user_profile in user_profiles:
        session.add(user_profile)

    session.flush()
    return user_profiles


def create_sample_ai_models(session: Session) -> List[AIModel]:
    """Create sample AI models.

    Args:
        session: SQLAlchemy session

    Returns:
        List of created AI model instances
    """
    ai_models = [
        AIModel(
            label="gpt-3.5-turbo",
            description="OpenAI's GPT-3.5 Turbo model for general purpose conversations.",
        ),
        AIModel(
            label="gpt-4",
            description="OpenAI's GPT-4 model for more advanced and nuanced conversations.",
        ),
        AIModel(
            label="claude-3-opus",
            description="Anthropic's Claude 3 Opus model, offering high performance and reliability.",
        ),
        AIModel(
            label="llama-3-70b",
            description="Meta's Llama 3 70B parameter model for local deployment.",
        ),
    ]

    for ai_model in ai_models:
        session.add(ai_model)

    session.flush()
    return ai_models


def create_sample_system_prompts(session: Session) -> List[SystemPrompt]:
    """Create sample system prompts.

    Args:
        session: SQLAlchemy session

    Returns:
        List of created system prompt instances
    """
    system_prompts = [
        SystemPrompt(
            label="basic_roleplay",
            content="You are roleplaying as the character described. Stay in character at all times.",
        ),
        SystemPrompt(
            label="detailed_roleplay",
            content=(
                "You are roleplaying as the character described. Stay in character at all times. "
                "Use the character's typical speech patterns, vocabulary, and mannerisms. "
                "Reference events and knowledge that would be familiar to this character."
            ),
        ),
        SystemPrompt(
            label="creative_writing",
            content=(
                "You are roleplaying as the character described. Write responses in a creative, "
                "engaging narrative style while maintaining the character's voice and personality."
            ),
        ),
    ]

    for system_prompt in system_prompts:
        session.add(system_prompt)

    session.flush()
    return system_prompts


def create_sample_chat_sessions(
    session: Session,
    characters: List[Character],
    user_profiles: List[UserProfile],
    ai_models: List[AIModel],
    system_prompts: List[SystemPrompt],
) -> List[ChatSession]:
    """Create sample chat sessions.

    Args:
        session: SQLAlchemy session
        characters: List of character instances
        user_profiles: List of user profile instances
        ai_models: List of AI model instances
        system_prompts: List of system prompt instances

    Returns:
        List of created chat session instances
    """
    # Create a few sample combinations for chat sessions
    chat_sessions = [
        ChatSession(
            character_id=characters[0].id,  # Sherlock Holmes
            user_profile_id=user_profiles[1].id,  # Detective
            ai_model_id=ai_models[1].id,  # GPT-4
            system_prompt_id=system_prompts[1].id,  # Detailed roleplay
            pre_prompt="Remember you are Sherlock Holmes, the detective.",
            pre_prompt_enabled=True,
            post_prompt=None,
            post_prompt_enabled=False,
            start_time=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(hours=6),
        ),
        ChatSession(
            character_id=characters[3].id,  # Hermione Granger
            user_profile_id=user_profiles[2].id,  # Student
            ai_model_id=ai_models[2].id,  # Claude 3 Opus
            system_prompt_id=system_prompts[0].id,  # Basic roleplay
            pre_prompt=None,
            pre_prompt_enabled=False,
            post_prompt="Keep responses educational and helpful.",
            post_prompt_enabled=True,
            start_time=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(hours=2),
        ),
        ChatSession(
            character_id=characters[4].id,  # Yoda
            user_profile_id=user_profiles[0].id,  # Default user
            ai_model_id=ai_models[0].id,  # GPT-3.5 Turbo
            system_prompt_id=system_prompts[2].id,  # Creative writing
            pre_prompt="Speak in Yoda's distinctive syntax.",
            pre_prompt_enabled=True,
            post_prompt="Include Star Wars wisdom in your response.",
            post_prompt_enabled=True,
            start_time=datetime.now() - timedelta(hours=12),
            updated_at=datetime.now() - timedelta(minutes=30),
        ),
    ]

    for chat_session in chat_sessions:
        session.add(chat_session)

    session.flush()
    return chat_sessions


def create_sample_messages(session: Session, chat_sessions: List[ChatSession]) -> None:
    """Create sample messages for chat sessions.

    Args:
        session: SQLAlchemy session
        chat_sessions: List of chat session instances
    """
    # Sample conversation data for each chat session
    conversations: Dict[int, List[tuple]] = {
        # Sherlock Holmes conversation
        chat_sessions[0].id: [
            (MessageRole.USER, "Hello, Mr. Holmes. I have a case for you."),
            (
                MessageRole.ASSISTANT,
                "Indeed? Pray tell me the details, and omit nothing, no matter how trivial "
                "it may seem. The smallest trifles are often the most significant.",
            ),
            (
                MessageRole.USER,
                "My valuable pocket watch has disappeared from my locked study.",
            ),
            (
                MessageRole.ASSISTANT,
                "Interesting. Was there any sign of forced entry? And do tell me, who has had "
                "access to your study in the past 24 hours? The timing of the disappearance "
                "may be most illuminating.",
            ),
            (MessageRole.USER, "No forced entry. Only my butler and maid have keys."),
            (
                MessageRole.ASSISTANT,
                "Ah! Then our field of inquiry narrows considerably. It must be either an "
                "inside job or a case of remarkable ingenuity. Tell me about these servants - "
                "how long have they been in your employment? Have you noticed any unusual "
                "behavior recently? And most importantly, was there anything distinctive about "
                "this pocket watch that might make it traceable?",
            ),
        ],
        # Hermione Granger conversation
        chat_sessions[1].id: [
            (
                MessageRole.USER,
                "Hi Hermione, can you help me with my Potions homework?",
            ),
            (
                MessageRole.ASSISTANT,
                "Of course! Potions can be quite tricky, but with the right approach, it's "
                "perfectly manageable. What specific aspect are you struggling with? Is it "
                "ingredient properties, brewing techniques, or perhaps understanding the "
                "theoretical principles?",
            ),
            (
                MessageRole.USER,
                "I don't understand the difference between infusion and decoction methods.",
            ),
            (
                MessageRole.ASSISTANT,
                "Oh, that's a common confusion! Let me explain. An infusion involves steeping "
                "ingredients in liquid, usually hot water, without boiling. It's gentler and "
                "preserves volatile magical properties. Think of how we make tea!\n\n"
                "A decoction, however, involves actively boiling the ingredients, often for "
                "an extended period. This method extracts deeper, more stubborn properties "
                "from hardy ingredients like roots and bark.\n\n"
                "Professor Snape would expect you to know that infusions are used for delicate "
                "ingredients like flowers and leaves, while decoctions are for tougher materials. "
                "The choice dramatically affects potion potency and stability!",
            ),
            (MessageRole.USER, "That makes sense! When would I use each method?"),
            (
                MessageRole.ASSISTANT,
                "I'm glad it's clearer now! Here's when you'd use each method:\n\n"
                "Use INFUSIONS when:\n"
                "- Working with delicate ingredients (flowers, leaves, feathers)\n"
                "- The magical property is easily extracted\n"
                "- You need to preserve volatile compounds\n"
                "- The potion requires subtlety and finesse\n"
                "- Examples: Draught of Peace, Euphoria Elixir\n\n"
                "Use DECOCTIONS when:\n"
                "- Working with tough ingredients (roots, bark, horns)\n"
                "- The magical property is deeply embedded\n"
                "- You need maximum strength extraction\n"
                "- The potion requires stability and potency\n"
                "- Examples: Polyjuice Potion, Skele-Gro\n\n"
                "Oh! And remember to note this in your essay - some advanced potions use "
                "BOTH methods at different stages. That always impresses the examiners!",
            ),
        ],
        # Yoda conversation
        chat_sessions[2].id: [
            (MessageRole.USER, "Master Yoda, I'm feeling lost. How do I find my path?"),
            (
                MessageRole.ASSISTANT,
                "Lost, you feel? Hmm. Natural, this is. Clear, your path never is, "
                "until behind you it lies. Trust in the Force, you must. Within you, "
                "the answers already exist. Still your mind. Listen, not with ears, but with heart.",
            ),
            (MessageRole.USER, "But how do I know what the right choice is?"),
            (
                MessageRole.ASSISTANT,
                "The right choice, hmm? Always in motion, the future is. No certainty, "
                "there can be. Feel, don't think. Trust your instincts, you should. "
                "When quiet your mind is, speak to you the Force will. Fear of choosing wrong, "
                "let go you must. Fear is the path to the dark side. Clouded by fear, "
                "your judgment becomes.",
            ),
            (MessageRole.USER, "I'm afraid of failing those who depend on me."),
            (
                MessageRole.ASSISTANT,
                "Mmmm. Understand this, I do. Heavy, the burden of others' expectations is. "
                "But remember you must - fail them you will, if guided by fear your actions are. "
                "Serve others best, we do, when true to ourselves we remain. "
                "Failure? Heh! The greatest teacher, failure is. Learn from it, we do. "
                "Grow from it, we must. Worry about failing others, you should not. "
                "Worry about failing yourself, you should not. Do or do not, there is no try. "
                "In the moment, be. The right path, reveal itself it will.",
            ),
        ],
    }

    # Create messages for each chat session with appropriate timestamps
    for chat_session_id, conversation in conversations.items():
        base_time = datetime.now() - timedelta(hours=random.randint(1, 24))

        for i, (role, content) in enumerate(conversation):
            # Each message is 2-5 minutes after the previous one
            message_time = base_time + timedelta(minutes=(i * random.randint(2, 5)))

            message = Message(
                chat_session_id=chat_session_id,
                role=role,
                content=content,
                timestamp=message_time,
            )
            session.add(message)


def create_application_settings(
    session: Session,
    user_profiles: List[UserProfile],
    ai_models: List[AIModel],
    system_prompts: List[SystemPrompt],
) -> None:
    """Create application settings with default values.

    Args:
        session: SQLAlchemy session
        user_profiles: List of user profile instances
        ai_models: List of AI model instances
        system_prompts: List of system prompt instances
    """
    # Get or create application settings
    app_settings = ApplicationSettings.get_instance(session)

    # Set default values
    app_settings.default_user_profile_id = user_profiles[0].id  # Default user
    app_settings.default_ai_model_id = ai_models[0].id  # GPT-3.5 Turbo
    app_settings.default_system_prompt_id = system_prompts[0].id  # Basic roleplay
    app_settings.default_avatar_image = ""

    session.add(app_settings)


def load_sample_data() -> None:
    """Load all sample data into the database."""
    with session_scope() as session:
        print("Creating sample characters...")
        characters = create_sample_characters(session)

        print("Creating sample user profiles...")
        user_profiles = create_sample_user_profiles(session)

        print("Creating sample AI models...")
        ai_models = create_sample_ai_models(session)

        print("Creating sample system prompts...")
        system_prompts = create_sample_system_prompts(session)

        print("Creating sample chat sessions...")
        chat_sessions = create_sample_chat_sessions(
            session, characters, user_profiles, ai_models, system_prompts
        )

        print("Creating sample messages...")
        create_sample_messages(session, chat_sessions)

        print("Creating application settings...")
        create_application_settings(session, user_profiles, ai_models, system_prompts)

        print("Sample data loaded successfully!")


if __name__ == "__main__":
    load_sample_data()

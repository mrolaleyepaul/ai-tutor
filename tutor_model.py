import os
from typing import List, Literal, TypedDict
from google import genai
from google.genai import types

from system_prompt import SYSTEM_PROMPT

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set. "
        "Set it before starting the server: export GEMINI_API_KEY=your-key"
    )

MODEL_NAME = "gemini-2.5-flash"

client = genai.Client(api_key=API_KEY)

class ChatTurn(TypedDict):
    """One turn of conversation history, as the backend should send it."""
    role: Literal["user", "model"]
    text: str


def _history_to_contents(history: List[ChatTurn]) -> List[types.Content]:
    """Convert the backend's simple history format into Gemini's expected shape."""
    contents = []
    for turn in history:
        contents.append(
            types.Content(
                role=turn["role"],
                parts=[types.Part(text=turn["text"])],
            )
        )
    return contents

def get_tutor_reply(history: List[ChatTurn], user_message: str) -> str:
    """
    Core model function.

    Args:
        history: prior conversation turns, oldest first. Empty list on first
                 message of a session. Each item: {"role": "user"|"model", "text": str}
        user_message: the new message from the learner.

    Returns:
        The tutor's reply as plain text.
    """
    contents = _history_to_contents(history)
    contents.append(
        types.Content(role="user", parts=[types.Part(text=user_message)])
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=1024,
        ),
    )

    return response.text
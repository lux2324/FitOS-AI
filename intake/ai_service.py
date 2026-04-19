import json
from openai import OpenAI
from django.conf import settings


ANALYSIS_PROMPT = """You are a gym training coach assistant. Analyze the user's intake text and extract structured data.

You receive 3 text fields from a new client:
- training_story: their training history
- limitations_story: injuries, pain, physical limitations
- extra_notes: anything else they mentioned

Extract and return ONLY valid JSON with this exact structure:

{
  "training_background": {
    "has_gym_experience": true/false,
    "training_style": "bodybuilding|crossfit|sport_specific|casual_gym|home_training|none",
    "known_exercises": ["list of exercises they mention knowing"],
    "longest_streak": "estimate how long their longest consistent period was, e.g. '6 months', 'unknown'"
  },
  "limitations": {
    "avoid_body_parts": ["list of body parts to be careful with, e.g. 'lower_back', 'left_shoulder', 'right_knee'"],
    "avoid_movements": ["specific movements to avoid, e.g. 'overhead_press', 'deep_squat', 'deadlift'"],
    "severity": "none|mild|moderate|serious",
    "notes": "brief summary of limitations in one sentence"
  },
  "coach_notes": "one sentence summary of anything else relevant for building their plan"
}

Rules:
- If a field is empty or the user wrote nothing useful, use sensible defaults (empty lists, "none", "unknown")
- Do NOT invent information. Only extract what the user actually wrote.
- Keep avoid_body_parts and avoid_movements as lowercase_snake_case
- Be conservative with severity — only mark "serious" if user describes major surgery, chronic pain, or medical conditions
- Return ONLY the JSON, no markdown, no explanation"""


def analyze_intake_text(training_story: str, limitations_story: str, extra_notes: str) -> dict | None:
    """Send intake text to OpenAI and return structured analysis."""

    combined = ""
    if training_story.strip():
        combined += f"TRAINING STORY:\n{training_story.strip()}\n\n"
    if limitations_story.strip():
        combined += f"LIMITATIONS:\n{limitations_story.strip()}\n\n"
    if extra_notes.strip():
        combined += f"EXTRA NOTES:\n{extra_notes.strip()}\n\n"

    if not combined.strip():
        return {
            "training_background": {
                "has_gym_experience": False,
                "training_style": "none",
                "known_exercises": [],
                "longest_streak": "unknown",
            },
            "limitations": {
                "avoid_body_parts": [],
                "avoid_movements": [],
                "severity": "none",
                "notes": "No limitations reported.",
            },
            "coach_notes": "No additional information provided.",
        }

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ANALYSIS_PROMPT},
                {"role": "user", "content": combined},
            ],
            temperature=0.2,
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e)}

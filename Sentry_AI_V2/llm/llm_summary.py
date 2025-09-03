import os
import requests
import json
from dotenv import load_dotenv

# Load .env variables
load_dotenv()


# -------------------- Gemini API Config --------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# -------------------- Generate Summary --------------------
def generate_summary_from_events(event_buffer):
    """
    Generates a textual summary of events using Gemini LLM API.

    Args:
        event_buffer (list): List of dicts, each containing:
                             {'frame': int, 'yolo': str, 'i3d': str, 'final': str}

    Returns:
        str: LLM-generated summary
    """
    if not GEMINI_API_KEY:
        raise Exception("GEMINI_API_KEY is not set or empty!")

    # Prepare input text for LLM
    text_input = "Summarize the following events detected by Mini SentryAI+:\n\n"
    for ev in event_buffer:
        text_input += f"Frame: {ev['frame']}, YOLO: {ev['yolo']}, I3D: {ev['i3d']}, Final Severity: {ev['final']}\n"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": text_input}
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    # Send POST request to Gemini API
    response = requests.post(GEMINI_URL, headers=headers, data=json.dumps(payload))

    # Handle HTTP errors
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.status_code} {response.text}")

    result = response.json()

    # Parse the text output from Gemini response
    try:
        summary_text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise Exception(f"Unexpected Gemini API response structure: {result}")

    return summary_text

# -------------------- Test Run --------------------
if __name__ == "__main__":
    # Quick test
    dummy_events = [
        {"frame": 100, "yolo": "fire", "i3d": "normal", "final": "danger"},
        {"frame": 150, "yolo": "knife", "i3d": "fighting", "final": "suspicious"},
    ]
    summary = generate_summary_from_events(dummy_events)
    print("LLM Summary:\n", summary)

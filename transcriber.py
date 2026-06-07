"""
Audio transcription using Google Gemini API.
Downloads the audio file from Twilio's media URL and sends it to Gemini.
"""

import os
import tempfile
import requests
from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")


def transcribe_audio(media_url: str) -> str:
    """
    Download an audio file from Twilio and transcribe it with Gemini.
    Returns the Hebrew transcript as a string.
    """
    # Download the audio file (Twilio requires authentication)
    response = requests.get(
        media_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=60,
        proxies={"https": os.environ.get("HTTPS_PROXY"), "http": os.environ.get("HTTP_PROXY")} if os.environ.get("HTTPS_PROXY") else None,
    )
    response.raise_for_status()

    # Determine file extension from content-type
    content_type = response.headers.get("Content-Type", "audio/ogg")
    ext_map = {
        "audio/ogg": ".ogg",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/wav": ".wav",
        "audio/webm": ".webm",
        "audio/amr": ".amr",
    }
    ext = next((v for k, v in ext_map.items() if k in content_type), ".ogg")
    mime_type = content_type.split(";")[0].strip()

    # Save to a temp file
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = _client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                language="he",
            )
        return transcription.text.strip()
    finally:
        os.unlink(tmp_path)

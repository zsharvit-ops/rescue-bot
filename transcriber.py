"""
Audio transcription using Google Gemini API.
Downloads the audio file from Twilio's media URL and sends it to Gemini.
"""

import os
import tempfile
import requests
import google.genai as genai

_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
        audio_file = _client.files.upload(
            file=tmp_path,
            config=genai.types.UploadFileConfig(mime_type=mime_type),
        )
        result = _client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                audio_file,
                "תמלל את ההקלטה הזו לעברית. החזר רק את הטקסט המתומלל, ללא הסברים.",
            ],
        )
        return result.text.strip()
    finally:
        os.unlink(tmp_path)

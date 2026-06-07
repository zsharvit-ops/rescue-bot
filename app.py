"""
WhatsApp Search & Rescue Bot
Receives a conversation transcript via WhatsApp, extracts victim info using GPT,
and returns a formatted .docx report.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from extractor import extract_fields, generate_summary, format_transcript_with_speakers
from pdf_generator import generate_pdf
from transcriber import transcribe_audio
import tempfile
import requests as http_requests
import threading

app = Flask(__name__)

# Twilio credentials (set in .env or environment variables)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# In-memory session store: {from_number: {"buffer": str, "collecting": bool}}
sessions = {}

TRIGGER_PHRASE = "תמלול:"  # User sends "תמלול:" followed by the transcript

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")
    num_media = int(request.form.get("NumMedia", 0))
    print(f"[webhook] from={from_number} num_media={num_media} body={incoming_msg[:50]!r}", flush=True)

    resp = MessagingResponse()
    msg = resp.message()

    # ── Audio message received (voice recording) ─────────────────────────
    if num_media > 0:
        media_url = request.form.get("MediaUrl0", "")
        media_type = request.form.get("MediaContentType0", "")

        if "audio" in media_type or "ogg" in media_type or "mpeg" in media_type or "mp4" in media_type:
            msg.body("🎙️ קיבלתי הקלטה! מתמלל... אנא המתן מספר שניות.")
            threading.Thread(
                target=_transcribe_and_reply,
                args=(media_url, from_number),
                daemon=True,
            ).start()
        else:
            msg.body("⚠️ קיבלתי קובץ אך הוא אינו אודיו. אנא שלח קובץ הקלטה (.ogg, .mp3, .m4a).")
        return str(resp)

    # ── Text: trigger phrase ──────────────────────────────────────────────
    if incoming_msg.startswith(TRIGGER_PHRASE):
        transcript = incoming_msg[len(TRIGGER_PHRASE):].strip()
        sessions[from_number] = {"buffer": transcript, "collecting": True}

        if len(transcript) > 50:
            msg.body("⏳ מעבד את התמלול... אשלח לך את המסמך תוך שניות.")
            threading.Thread(
                target=_process_and_reply,
                args=(from_number, transcript),
                daemon=True,
            ).start()
        else:
            msg.body(
                "📋 התחלתי לקבל את התמלול. שלח את שאר הטקסט, "
                "ולסיום שלח את המילה: *סיום*"
            )
        return str(resp)

    # ── Accumulation mode ────────────────────────────────────────────────
    if from_number in sessions and sessions[from_number].get("collecting"):
        if incoming_msg.lower() in ("סיום", "done", "finish"):
            transcript = sessions.pop(from_number, {}).get("buffer", "")
            msg.body("⏳ מעבד את התמלול... אשלח לך את המסמך תוך שניות.")
            threading.Thread(
                target=_process_and_reply,
                args=(from_number, transcript),
                daemon=True,
            ).start()
        else:
            sessions[from_number]["buffer"] += "\n" + incoming_msg
            msg.body("✅ קיבלתי. המשך לשלוח או שלח *סיום* לסיום.")
        return str(resp)

    # ── Default help ──────────────────────────────────────────────────────
    msg.body(
        "👋 ברוך הבא לבוט תחקיר חילוץ.\n\n"
        "שלח לי:\n"
        "🎙️ *קובץ הקלטה* — אתמלל אוטומטית ואוציא דוח\n"
        "📝 *תמלול:* [טקסט] — לעיבוד טקסט ידני\n\n"
        "לסיום הודעות מרובות שלח: *סיום*"
    )
    return str(resp)


def _process_and_reply(from_number: str, transcript: str):
    """Background thread: extract fields, generate doc, send via Twilio client."""
    print(f"[_process_and_reply] START for {from_number}", flush=True)
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        print("[_process_and_reply] extracting fields...", flush=True)
        fields = extract_fields(transcript)
        print("[_process_and_reply] generating summary...", flush=True)
        summary = generate_summary(transcript)
        print("[_process_and_reply] formatting transcript by speakers...", flush=True)
        formatted_transcript = format_transcript_with_speakers(transcript)
        print("[_process_and_reply] generating pdf...", flush=True)
        doc_path = generate_pdf(fields, formatted_transcript, summary=summary)

        os.makedirs("static/output", exist_ok=True)
        import shutil
        file_name = os.path.basename(doc_path)
        dest = os.path.join("static", "output", file_name)
        shutil.copy(doc_path, dest)

        host = os.environ.get("PUBLIC_URL", "http://localhost:5000").rstrip("/")
        doc_url = f"{host}/static/output/{file_name}"
        print(f"[_process_and_reply] sending doc_url={doc_url}", flush=True)

        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=from_number,
            body=f"📄 דוח תחקיר חילוץ מוכן!\nלחץ לצפייה/הורדה:\n{doc_url}",
        )
        print("[_process_and_reply] DONE", flush=True)
    except Exception as e:
        print(f"[_process_and_reply] ERROR: {e}", flush=True)
        err_msg = f"\u274c שגיאה בעיבוד:\n{str(e)[:200]}"
        try:
            client.messages.create(from_=TWILIO_WHATSAPP_NUMBER, to=from_number, body=err_msg)
        except Exception:
            pass


def _transcribe_and_reply(media_url: str, from_number: str):
    """Run in background thread: transcribe audio then send doc."""
    print(f"[_transcribe_and_reply] START downloading {media_url}", flush=True)
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        transcript = transcribe_audio(media_url)
        print(f"[_transcribe_and_reply] transcript={transcript[:80]}", flush=True)
        _process_and_reply(from_number, transcript)
    except Exception as e:
        print(f"[_transcribe_and_reply] ERROR: {e}", flush=True)
        err_msg = f"\u274c שגיאה בתמלול ההקלטה:\n{str(e)[:200]}"
        try:
            client.messages.create(from_=TWILIO_WHATSAPP_NUMBER, to=from_number, body=err_msg)
        except Exception:
            pass


def _process_transcript_and_reply(from_number: str, transcript: str):
    """Used after audio transcription — sends result directly via Twilio client."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    print(f"DEBUG from_={TWILIO_WHATSAPP_NUMBER!r} to={from_number!r}", flush=True)
    try:
        fields = extract_fields(transcript)
        doc_path = generate_doc(fields, transcript)

        os.makedirs("static/output", exist_ok=True)
        import shutil
        file_name = os.path.basename(doc_path)
        dest = os.path.join("static", "output", file_name)
        shutil.copy(doc_path, dest)

        host = os.environ.get("PUBLIC_URL", "http://localhost:5000").rstrip("/")
        doc_url = f"{host}/static/output/{file_name}"

        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=from_number,
            body=f"📄 דוח תחקיר חילוץ מוכן (הופק מהקלטה)!\nלחץ להורדה:\n{doc_url}",
        )
    except Exception as e:
        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=from_number,
            body=f"❌ שגיאה בעיבוד ההקלטה:\n{e}",
        )


def _process_transcript(from_number: str, msg):
    """Extract fields, generate doc, and send back via Twilio MMS."""
    transcript = sessions.pop(from_number, {}).get("buffer", "")
    if not transcript:
        msg.body("❌ לא קיבלתי תמלול. אנא נסה שנית.")
        return

    msg.body("⏳ מעבד את התמלול... אשלח לך את המסמך תוך שניות.")

    try:
        fields = extract_fields(transcript)
        doc_path = generate_doc(fields, transcript)

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print(f"DEBUG from_={TWILIO_WHATSAPP_NUMBER!r} to={from_number!r}", flush=True)
        file_name = os.path.basename(doc_path)
        os.makedirs("static/output", exist_ok=True)
        import shutil
        dest = os.path.join("static", "output", file_name)
        shutil.copy(doc_path, dest)

        host = os.environ.get("PUBLIC_URL", "http://localhost:5000").rstrip("/")
        doc_url = f"{host}/static/output/{file_name}"

        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=from_number,
            body=f"📄 דוח תחקיר חילוץ מוכן!\nלחץ להורדה:\n{doc_url}",
        )
    except Exception as e:
        msg.body(f"❌ שגיאה בעיבוד התמלול:\n{e}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", debug=False, port=port)

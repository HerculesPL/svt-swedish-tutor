"""
Workout Ingestion API — Vercel Serverless Function
Endpoint: POST /api/workout

Receives Apple Watch workout JSON from an Apple Shortcut,
then forwards it to the user's Telegram chat as a file
so OpenClaw can process it with the workout-coach skill.

Required environment variables (set in Vercel dashboard):
  TELEGRAM_BOT_TOKEN  — your Telegram bot token
  TELEGRAM_CHAT_ID    — your Telegram user ID
"""

import json
import os
import uuid
import urllib.request
from http.server import BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_workout_to_telegram(data: bytes):
    """Send the workout JSON to Telegram as a document file."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars.")

    boundary = uuid.uuid4().hex
    filename = "workout.json"

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{TELEGRAM_CHAT_ID}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'
        f"Content-Type: application/json\r\n\r\n"
    ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Validate it's proper JSON before forwarding
            json.loads(body)

            result = send_workout_to_telegram(body)

            if not result.get("ok"):
                raise ValueError(f"Telegram API error: {result}")

            self._respond(200, {"ok": True, "message": "Workout sent to Telegram."})

        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON payload."})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

    def log_message(self, format, *args):
        pass

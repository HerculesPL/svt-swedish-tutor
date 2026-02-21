"""
SVT Transcript API — Vercel Serverless Function
Endpoint: GET /api/transcript?id=jXvkPLJ
          GET /api/transcript?url=https://www.svtplay.se/video/jXvkPLJ/...

Returns a clean timestamped transcript as plain text.
"""

import re
import json
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


# ── Core logic ────────────────────────────────────────────────────────────────

def extract_video_id(value: str) -> str:
    """Accept either a raw video ID or a full SVT Play URL."""
    if value.startswith("http"):
        match = re.search(r"/video/([^/?#]+)", value)
        if not match:
            raise ValueError("Could not extract video ID from URL.")
        return match.group(1)
    return value.strip()


def fetch_metadata(video_id: str) -> dict:
    url = f"https://api.svt.se/video/{video_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; svt-transcript-api/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_subtitle_url(metadata: dict) -> str:
    subtitles = metadata.get("subtitleReferences", [])
    # Prefer Swedish
    for sub in subtitles:
        if sub.get("language", "").lower() in ("sv", "swe", "swedish") and sub.get("url"):
            return sub["url"]
    # Fallback to first available
    for sub in subtitles:
        if sub.get("url"):
            return sub["url"]
    raise ValueError("No subtitles found for this episode.")


def fetch_vtt(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; svt-transcript-api/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8")


def parse_vtt(vtt: str) -> list:
    lines = vtt.splitlines()
    cues = []
    i = 0

    while i < len(lines) and not lines[i].strip().startswith("WEBVTT"):
        i += 1
    i += 1

    while i < len(lines):
        if not lines[i].strip() or lines[i].strip().startswith("NOTE"):
            i += 1
            continue
        if "-->" not in lines[i] and i + 1 < len(lines) and "-->" in lines[i + 1]:
            i += 1
            continue
        if "-->" in lines[i]:
            start = lines[i].strip().split("-->")[0].strip().split()[0]
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            raw = " ".join(text_lines)
            clean = re.sub(r"<[^>]+>", "", raw)
            clean = re.sub(r"\{[^}]+\}", "", clean).strip()
            if clean:
                cues.append({"start": start, "text": clean})
        else:
            i += 1

    return cues


def deduplicate(cues: list) -> list:
    seen = []
    result = []
    for cue in cues:
        if cue["text"] not in seen:
            seen.append(cue["text"])
            if len(seen) > 5:
                seen.pop(0)
            result.append(cue)
    return result


def build_transcript(cues: list) -> str:
    return "\n".join(f"[{c['start']}]  {c['text']}" for c in cues)


def get_transcript(video_id_or_url: str) -> str:
    video_id = extract_video_id(video_id_or_url)
    metadata = fetch_metadata(video_id)
    subtitle_url = find_subtitle_url(metadata)
    vtt = fetch_vtt(subtitle_url)
    cues = deduplicate(parse_vtt(vtt))
    return build_transcript(cues)


# ── Vercel handler ─────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Accept ?id=jXvkPLJ or ?url=https://...
        video_input = None
        if "id" in params:
            video_input = params["id"][0]
        elif "url" in params:
            video_input = params["url"][0]

        if not video_input:
            self._respond(400, {"error": "Missing required parameter: id or url"})
            return

        try:
            transcript = get_transcript(video_input)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(transcript.encode("utf-8"))
        except ValueError as e:
            self._respond(400, {"error": str(e)})
        except Exception as e:
            self._respond(500, {"error": f"Internal error: {str(e)}"})

    def _respond(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Suppress default request logging

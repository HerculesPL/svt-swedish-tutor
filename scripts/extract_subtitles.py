#!/usr/bin/env python3
"""
SVT Play Subtitle Extractor
Usage: python extract_subtitles.py <svt_play_url>

Extracts Swedish subtitles from an SVT Play episode and saves them
as a clean text transcript.
"""

import sys
import re
import json
import urllib.request
import urllib.error


def get_video_id(url: str) -> str:
    """Extract the video ID from an SVT Play URL."""
    # Matches IDs like jXvkPLJ from URLs like
    # https://www.svtplay.se/video/jXvkPLJ/show-name/episode-name
    match = re.search(r"/video/([^/]+)", url)
    if not match:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    return match.group(1)


def fetch_video_metadata(video_id: str) -> dict:
    """Fetch video metadata from SVT's API."""
    api_url = f"https://api.svt.se/video/{video_id}"
    req = urllib.request.Request(
        api_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; SVT subtitle extractor)"}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def find_subtitle_url(metadata: dict):
    """Find the Swedish subtitle URL from the metadata."""
    subtitles = metadata.get("subtitleReferences", [])
    
    # Prefer Swedish subtitles, fall back to any available
    for sub in subtitles:
        lang = sub.get("language", "").lower()
        url = sub.get("url", "")
        if lang in ("sv", "swe", "swedish") and url:
            return url
    
    # Fallback: return first available subtitle
    for sub in subtitles:
        url = sub.get("url", "")
        if url:
            print(f"Note: Using subtitle language '{sub.get('language', 'unknown')}' (no Swedish found)")
            return url
    
    return None


def fetch_subtitle_file(url: str):
    """Download the subtitle file content."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; SVT subtitle extractor)"}
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def parse_vtt(vtt_content: str):
    """Parse a WebVTT file into a list of cue entries with timestamps and text."""
    lines = vtt_content.splitlines()
    cues = []
    i = 0

    # Skip WEBVTT header
    while i < len(lines) and not lines[i].strip().startswith("WEBVTT"):
        i += 1
    i += 1

    while i < len(lines):
        # Skip blank lines and NOTE blocks
        if not lines[i].strip() or lines[i].strip().startswith("NOTE"):
            i += 1
            continue

        # Skip cue IDs (numeric or alphanumeric identifiers before timestamps)
        if "-->" not in lines[i] and i + 1 < len(lines) and "-->" in lines[i + 1]:
            i += 1
            continue

        # Parse timestamp line
        if "-->" in lines[i]:
            timestamp_line = lines[i].strip()
            start, _, end = timestamp_line.partition("-->")
            start = start.strip().split()[0]  # Remove any extra settings
            end = end.strip().split()[0]

            # Collect cue text lines
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1

            # Clean up HTML tags and formatting codes
            raw_text = " ".join(text_lines)
            clean_text = re.sub(r"<[^>]+>", "", raw_text)  # Remove HTML tags
            clean_text = re.sub(r"\{[^}]+\}", "", clean_text)  # Remove formatting codes
            clean_text = clean_text.strip()

            if clean_text:
                cues.append({
                    "start": start,
                    "end": end,
                    "text": clean_text
                })
        else:
            i += 1

    return cues


def deduplicate_cues(cues):
    """Remove duplicate or overlapping subtitle lines."""
    seen = []
    result = []
    for cue in cues:
        if cue["text"] not in seen:
            seen.append(cue["text"])
            if len(seen) > 5:
                seen.pop(0)
            result.append(cue)
    return result


def build_transcript(cues, include_timestamps: bool = True):
    """Build a readable transcript from cue entries."""
    lines = []
    for cue in cues:
        if include_timestamps:
            lines.append(f"[{cue['start']}]  {cue['text']}")
        else:
            lines.append(cue["text"])
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_subtitles.py <svt_play_url> [--no-timestamps]")
        print("Example: python extract_subtitles.py https://www.svtplay.se/video/jXvkPLJ/sa-byggdes-sverige/...")
        sys.exit(1)

    url = sys.argv[1]
    include_timestamps = "--no-timestamps" not in sys.argv

    print(f"Extracting subtitles from: {url}")

    # Step 1: Get video ID
    video_id = get_video_id(url)
    print(f"Video ID: {video_id}")

    # Step 2: Fetch metadata
    print("Fetching video metadata...")
    metadata = fetch_video_metadata(video_id)

    # Step 3: Find subtitle URL
    subtitle_url = find_subtitle_url(metadata)
    if not subtitle_url:
        print("No subtitles found for this episode.")
        print("Available metadata keys:", list(metadata.keys()))
        sys.exit(1)

    print(f"Subtitle URL: {subtitle_url}")

    # Step 4: Download subtitle file
    print("Downloading subtitles...")
    vtt_content = fetch_subtitle_file(subtitle_url)

    # Step 5: Parse and clean
    print("Parsing subtitles...")
    cues = parse_vtt(vtt_content)
    cues = deduplicate_cues(cues)

    # Step 6: Build transcript
    transcript = build_transcript(cues, include_timestamps)

    # Step 7: Save to file
    output_filename = f"transcript_{video_id}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(transcript)

    print(f"\nDone! Saved {len(cues)} subtitle cues to: {output_filename}")
    print(f"Preview (first 5 lines):\n")
    for cue in cues[:5]:
        print(f"  [{cue['start']}] {cue['text']}")


if __name__ == "__main__":
    main()

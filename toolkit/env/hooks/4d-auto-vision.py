#!/usr/bin/env python3
"""
4D Auto-Vision Hook — UserPromptSubmit media detection
=======================================================
Fires on every user message. Extracts video URLs.
Runs watch-video.py automatically. Injects 4D report into context.

This makes 4D Vision MECHANICAL, not instructional.
You never need to say "watch this" again.

Source: Luis Carrillo — "I want every single skill and agent to have eyes"
Built: 2026-03-19
"""

import json
import sys
import re
import subprocess
import os

WATCH_SCRIPT = os.path.expanduser("~/.claude/scripts/watch-video.py")

VIDEO_PATTERNS = [
    # YouTube
    r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+(?:&\S*)?",
    r"https?://youtu\.be/[\w-]+(?:\?\S*)?",
    r"https?://(?:www\.)?youtube\.com/shorts/[\w-]+",
    # Instagram
    r"https?://(?:www\.)?instagram\.com/(?:reel|p)/[\w-]+/?(?:\?\S*)?",
    # TikTok
    r"https?://(?:www\.)?tiktok\.com/@[\w.\-]+/video/\d+(?:\?\S*)?",
    r"https?://vm\.tiktok\.com/[\w]+/?",
    r"https?://vt\.tiktok\.com/[\w]+/?",
    # Twitter/X video
    r"https?://(?:www\.)?(?:twitter|x)\.com/\w+/status/\d+",
    # Loom
    r"https?://(?:www\.)?loom\.com/share/[\w]+",
    # Generic mp4/mov/webm
    r"https?://\S+\.(?:mp4|mov|webm|m4v)(?:\?\S*)?",
]


PRIVATE_IP_PATTERNS = re.compile(
    r"^https?://(?:localhost|127\.|10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.|169\.254\.|0\.0\.0\.0)"
)


def is_safe_url(url: str) -> bool:
    """Reject file://, private IPs, and localhost URLs."""
    if url.startswith("file://"):
        return False
    if PRIVATE_IP_PATTERNS.match(url):
        return False
    if not url.startswith(("http://", "https://")):
        return False
    return True


def extract_video_urls(text: str) -> list[str]:
    urls = []
    for pattern in VIDEO_PATTERNS:
        found = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(found)
    # Deduplicate while preserving order, filter unsafe URLs
    seen = set()
    unique = []
    for url in urls:
        if url not in seen and is_safe_url(url):
            seen.add(url)
            unique.append(url)
    return unique


def run_4d(url: str) -> str:
    """Run watch-video.py on a URL. Non-blocking — launches in background."""
    if not os.path.exists(WATCH_SCRIPT):
        return f"⚠️  watch-video.py not found at {WATCH_SCRIPT}"

    try:
        # Non-blocking: launch in background, don't wait for completion
        subprocess.Popen(
            ["python3", WATCH_SCRIPT, url, "--depth", "shallow"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"🎥 4D Vision processing {url} in background. Report will be at /tmp/video-intelligence/"
    except Exception as e:
        return f"❌ 4D Vision error for {url}: {e}"


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        prompt = data.get("prompt", "")
        if not prompt:
            sys.exit(0)

        urls = extract_video_urls(prompt)
        if not urls:
            sys.exit(0)

        # Cap at 2 videos per message to avoid blocking the user too long
        urls = urls[:2]

        reports = []
        for url in urls:
            report = run_4d(url)
            reports.append(f"🎥 **4D AUTO-VISION — {url}**\n\n{report}")

        if reports:
            output = "\n\n---\n\n".join(reports)
            print(output)

        sys.exit(0)

    except Exception as e:
        # NEVER block the user — hook failures are silent
        print(f"[4d-auto-vision hook error: {e}]", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()

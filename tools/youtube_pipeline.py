"""
youtube_pipeline.py — Download YouTube videos, extract frames + transcripts,
caption frames with Claude vision, and generate structured game guidelines.

Usage:
    python3 tools/youtube_pipeline.py URL --output /path/to/output/dir
    python3 tools/youtube_pipeline.py URL --output /path --game "Game Name"

For each URL, a subdirectory named after the video ID is created under --output:
    <output>/<video_id>/
        frames/           — JPEG frames (one per 30 s)
        transcript.md     — full timestamped transcript
        captions.json     — per-frame captions referencing frame filenames
        guidelines.md     — structured game guidelines for QA testing

Dependencies (install once):
    pip install yt-dlp openai-whisper Pillow anthropic
    brew install ffmpeg   # also required by whisper
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import anthropic

_KEY_FILE = os.path.expanduser("~/projects/.anthropic_api_key")
if "ANTHROPIC_API_KEY" not in os.environ and os.path.exists(_KEY_FILE):
    os.environ["ANTHROPIC_API_KEY"] = open(_KEY_FILE).read().strip()

FRAME_INTERVAL_SECONDS = 30  # one frame per N seconds of video


# ---------------------------------------------------------------------------
# Step 1: Download
# ---------------------------------------------------------------------------

def _ytdlp() -> str:
    """Return the yt-dlp binary path."""
    candidates = [
        # pyenv 3.12 has the latest yt-dlp (2026.3.3+)
        os.path.expanduser("~/.pyenv/versions/3.12.2/bin/yt-dlp"),
        os.path.expanduser("~/.pyenv/shims/yt-dlp"),
        os.path.expanduser("~/Library/Python/3.12/bin/yt-dlp"),
        os.path.expanduser("~/Library/Python/3.11/bin/yt-dlp"),
        "/opt/homebrew/bin/yt-dlp",
        "/usr/local/bin/yt-dlp",
        os.path.expanduser("~/Library/Python/3.9/bin/yt-dlp"),
        "yt-dlp",
    ]
    for c in candidates:
        try:
            subprocess.run([c, "--version"], capture_output=True, check=True)
            return c
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("yt-dlp not found. Install with: pip install yt-dlp")


def _ffmpeg() -> str:
    """Return the ffmpeg binary path."""
    for candidate in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "ffmpeg"]:
        if os.path.isfile(candidate) or candidate == "ffmpeg":
            try:
                subprocess.run([candidate, "-version"], capture_output=True, check=True)
                return candidate
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
    raise RuntimeError("ffmpeg not found. Install with: brew install ffmpeg")


def video_id_from_url(url: str) -> str:
    """Extract YouTube video ID from a URL."""
    import re
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else url.split("/")[-1].split("?")[0]


def download_video(url: str, out_dir: str) -> str:
    """Download a YouTube video as MP4. Returns path to the downloaded file."""
    output_template = os.path.join(out_dir, "%(id)s.%(ext)s")
    ytdlp = _ytdlp()

    common = ["-o", output_template]

    # Strategies in order of reliability (updated 2026-03 — android client is most reliable)
    strategies = [
        # 1. Android client — bypasses SABR streaming, most reliable
        [ytdlp, "--extractor-args", "youtube:player_client=android",
         "--sleep-interval", "2", "-f", "bv*+ba/b"] + common + [url],
        # 2. Android + tv client combo
        [ytdlp, "--extractor-args", "youtube:player_client=android,tv",
         "--sleep-interval", "2", "-f", "bv*+ba/b"] + common + [url],
        # 3. Android with Chrome cookies
        [ytdlp, "--cookies-from-browser", "chrome",
         "--extractor-args", "youtube:player_client=android",
         "-f", "bv*+ba/b"] + common + [url],
        # 4. Android with Safari cookies
        [ytdlp, "--cookies-from-browser", "safari",
         "--extractor-args", "youtube:player_client=android",
         "-f", "bv*+ba/b"] + common + [url],
        # 5. iOS client
        [ytdlp, "--extractor-args", "youtube:player_client=ios",
         "-f", "bv*+ba/b"] + common + [url],
        # 6. Generic fallback with user-agent
        [ytdlp, "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
         "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
         "--merge-output-format", "mp4"] + common + [url],
        # 7. Bare fallback
        [ytdlp, "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
         "--merge-output-format", "mp4"] + common + [url],
    ]

    for cmd in strategies:
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode == 0:
            files = list(Path(out_dir).glob("*.mp4"))
            if files:
                return str(sorted(files)[0])

    raise RuntimeError(f"yt-dlp failed to download {url} (tried all strategies)")


# ---------------------------------------------------------------------------
# Step 1b: Playwright fallback — scrape frames from YouTube page
# ---------------------------------------------------------------------------

def scrape_youtube_frames(url: str, frame_dir: str, num_frames: int = 8) -> list[tuple[float, str]]:
    """
    Playwright fallback: navigate to the YouTube page, seek to N timestamps,
    and screenshot each frame. Works when video download is blocked.
    Returns list of (timestamp_s, image_path).
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print("  playwright not installed — run: pip install playwright && playwright install chromium")
        return []

    os.makedirs(frame_dir, exist_ok=True)
    frames: list[tuple[float, str]] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        # Load video page — auto-play is typically blocked; we seek manually
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Dismiss consent / cookie popups if present
        for selector in ['button[aria-label*="Accept"]', 'button[aria-label*="Reject"]',
                         '#yDmH0d .eom-button-row button', 'tp-yt-paper-button[aria-label*="agree"]']:
            try:
                page.click(selector, timeout=1500)
                page.wait_for_timeout(500)
            except Exception:
                pass

        # Click play to start the video, then pause it
        try:
            page.click('button.ytp-play-button', timeout=3000)
            page.wait_for_timeout(1500)
            page.click('button.ytp-play-button', timeout=3000)  # pause
        except Exception:
            pass

        # Get video duration from the player
        duration_s: float = 0.0
        try:
            dur_text = page.locator('.ytp-time-duration').inner_text(timeout=3000)
            parts = list(map(int, dur_text.split(':')))
            duration_s = parts[-1] + parts[-2] * 60 + (parts[-3] * 3600 if len(parts) > 2 else 0)
        except Exception:
            duration_s = 600.0  # assume 10 min if unknown

        # Seek to evenly spaced timestamps and screenshot
        step = duration_s / (num_frames + 1)
        for i in range(num_frames):
            ts = step * (i + 1)
            try:
                # Use YouTube's seekTo JS API
                page.evaluate(f"""
                    const v = document.querySelector('video');
                    if (v) {{ v.currentTime = {ts}; }}
                """)
                page.wait_for_timeout(1200)  # let frame render
                img_path = os.path.join(frame_dir, f"frame_{i+1:04d}.jpg")
                # Screenshot only the video element area
                video_el = page.locator('video').first
                video_el.screenshot(path=img_path)
                frames.append((ts, img_path))
                print(f"    Playwright frame {i+1}/{num_frames} @ {ts:.0f}s → {img_path}")
            except Exception as e:
                print(f"    Playwright frame {i+1} failed: {e}")

        browser.close()

    return frames


# ---------------------------------------------------------------------------
# Step 2: Extract frames with ffmpeg (no opencv needed)
# ---------------------------------------------------------------------------

def extract_frames(video_path: str, frame_dir: str, interval: int = FRAME_INTERVAL_SECONDS) -> list[tuple[float, str]]:
    """Extract one frame every `interval` seconds. Returns list of (timestamp_s, image_path)."""
    os.makedirs(frame_dir, exist_ok=True)
    subprocess.run(
        [
            _ffmpeg(), "-y",
            "-i", video_path,
            "-vf", f"fps=1/{interval}",
            "-q:v", "2",
            os.path.join(frame_dir, "frame_%04d.jpg"),
        ],
        check=True,
        capture_output=True,
    )
    frames = []
    for i, path in enumerate(sorted(Path(frame_dir).glob("frame_*.jpg"))):
        timestamp = i * interval
        frames.append((float(timestamp), str(path)))
    return frames


# ---------------------------------------------------------------------------
# Step 3: Transcribe audio with Whisper
# ---------------------------------------------------------------------------

def transcribe(video_path: str) -> list[dict]:
    """Run Whisper on the video. Returns list of segments {start, end, text}."""
    try:
        import whisper  # type: ignore
    except ImportError:
        print("openai-whisper not installed. Run: pip install openai-whisper", file=sys.stderr)
        raise

    print("  Loading Whisper model (small)...")
    model = whisper.load_model("small")
    print("  Transcribing...")
    result = model.transcribe(video_path)
    return result["segments"]


def transcript_window(segments: list[dict], start: float, duration: float = FRAME_INTERVAL_SECONDS) -> str:
    """Extract transcript text for [start, start+duration) seconds."""
    end = start + duration
    parts = [s["text"] for s in segments if s["start"] >= start and s["start"] < end]
    return " ".join(parts).strip()


def full_transcript(segments: list[dict]) -> str:
    return " ".join(s["text"] for s in segments).strip()


# ---------------------------------------------------------------------------
# Step 4: Caption each frame with Claude vision
# ---------------------------------------------------------------------------

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode()


def caption_frame(client: anthropic.Anthropic, image_b64: str, transcript_text: str) -> str:
    """Ask Claude to caption a frame given the accompanying transcript window."""
    content: list = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64},
        },
        {
            "type": "text",
            "text": (
                "You are captioning a board game tutorial video frame.\n"
                "Transcript for the next 30 seconds:\n"
                f"\"{transcript_text}\"\n\n"
                "Write one concise sentence (≤25 words) describing what is being "
                "demonstrated in this frame, combining what you see and what is being said."
            ),
        },
    ]
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=128,
        messages=[{"role": "user", "content": content}],
    )
    return resp.content[0].text.strip()


# ---------------------------------------------------------------------------
# Step 5: Generate game guidelines from transcript + sampled frames
# ---------------------------------------------------------------------------

def fetch_transcript_api(video_id: str) -> list[dict]:
    """Fetch transcript via youtube-transcript-api (no video download needed)."""
    from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    api = YouTubeTranscriptApi()
    snippets = list(api.fetch(video_id))
    return [{"start": s.start, "end": s.start + s.duration, "text": s.text} for s in snippets]


def generate_guidelines(
    client: anthropic.Anthropic,
    game_name: str,
    transcript_text: str,
    frames: list[tuple[float, str]],
    output_path: str,
) -> str:
    """Synthesize a structured game guidelines markdown document for testing."""
    content: list = []

    # Include up to 6 frames if available
    if frames:
        step = max(1, len(frames) // 6)
        for ts, img_path in frames[::step][:6]:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": encode_image(img_path)},
            })

    content.append({
        "type": "text",
        "text": (
            f"You are a game implementation expert. "
            + (f"The images above are frames from a '{game_name}' how-to-play tutorial video. " if frames else "")
            + f"Below is the full transcript of a '{game_name}' how-to-play video:\n\n"
            f"{transcript_text[:14000]}\n\n"
            f"Produce a structured markdown document titled '# {game_name} — Play Guidelines'.\n"
            "Include these sections:\n"
            "## Setup — board layout, piece placement, starting conditions\n"
            "## Turn Structure — exactly what a player does on their turn, in order\n"
            "## Valid Moves — precise conditions for each move type\n"
            "## Win Condition — how the game ends and who wins\n"
            "## Key Rules — any special rules, edge cases, or common mistakes\n"
            "## Testing Checklist — a bulleted list of game states / scenarios that a "
            "QA tester should verify in a digital implementation\n\n"
            "Be precise enough that a programmer can write automated tests from this document."
        ),
    })

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": content}],
    )
    text = resp.content[0].text.strip()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_video(url: str, video_out_dir: str, game_name: str, client: anthropic.Anthropic) -> None:
    """Full pipeline for one video URL. Saves all output to video_out_dir."""
    print(f"\n=== {url} ===")
    vid_id = video_id_from_url(url)
    frames: list[tuple[float, str]] = []

    # Step 1: Try to download video + extract frames (optional — may fail on YouTube)
    frame_dir = os.path.join(video_out_dir, "frames")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            print("  Downloading video (optional — skipped if blocked)...")
            video_path = download_video(url, tmp)
            frames = extract_frames(video_path, frame_dir)
            print(f"  {len(frames)} frames extracted")
            segments_whisper = transcribe(video_path)
    except Exception as e:
        print(f"  Video download/transcription skipped ({e})")
        segments_whisper = None

    # Step 1b: Playwright fallback — grab frames directly from YouTube page
    if not frames:
        print("  Trying Playwright scrape for frames...")
        frames = scrape_youtube_frames(url, frame_dir, num_frames=8)
        if frames:
            print(f"  {len(frames)} frames captured via Playwright")
        else:
            print("  Playwright frame capture also failed — proceeding without frames")

    # Step 2: Get transcript — use Whisper if available, else youtube-transcript-api
    if segments_whisper:
        segments = segments_whisper
        print(f"  Using Whisper transcript ({len(segments)} segments)")
    else:
        print("  Fetching transcript via youtube-transcript-api...")
        segments = fetch_transcript_api(vid_id)
        print(f"  {len(segments)} transcript segments fetched")

    # Step 3: Save transcript
    transcript_text = " ".join(s["text"] for s in segments)
    transcript_path = os.path.join(video_out_dir, "transcript.md")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcript\n\n**URL:** {url}\n\n")
        for s in segments:
            f.write(f"**[{s['start']:.1f}s]** {s['text'].strip()}\n\n")
    print(f"  Transcript saved → {transcript_path}")

    # Step 4: Caption frames (only if we have them)
    captions = []
    if frames:
        print("  Captioning frames with Claude...")
        for i, (ts, img_path) in enumerate(frames):
            print(f"    Frame {i+1}/{len(frames)} @ {ts:.0f}s")
            window = transcript_window(segments, ts)
            b64 = encode_image(img_path)
            caption = caption_frame(client, b64, window) if window else "(no transcript)"
            rel_frame = os.path.relpath(img_path, video_out_dir)
            captions.append({"timestamp_s": ts, "frame_file": rel_frame, "caption": caption})

    captions_path = os.path.join(video_out_dir, "captions.json")
    with open(captions_path, "w", encoding="utf-8") as f:
        json.dump({"url": url, "game": game_name, "has_frames": bool(frames), "captions": captions}, f, indent=2)
    print(f"  Captions saved → {captions_path}")

    # Step 5: Generate guidelines
    print("  Generating game guidelines with Claude...")
    guidelines_path = os.path.join(video_out_dir, "guidelines.md")
    generate_guidelines(client, game_name, transcript_text, frames, guidelines_path)
    print(f"  Guidelines saved → {guidelines_path}")


def run_pipeline(urls: list[str], output_dir: str, game_name: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    client = anthropic.Anthropic()

    for url in urls:
        vid_id = video_id_from_url(url)
        video_out_dir = os.path.join(output_dir, vid_id)
        os.makedirs(video_out_dir, exist_ok=True)
        process_video(url, video_out_dir, game_name, client)

    print("\nDone. Output structure:")
    for url in urls:
        vid_id = video_id_from_url(url)
        print(f"  {output_dir}/{vid_id}/  ← {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube → captioned frames + game guidelines")
    parser.add_argument("urls", nargs="+", help="YouTube URLs to process")
    parser.add_argument("--output", required=True, help="Directory to write output files")
    parser.add_argument("--game", default="Unknown Game", help="Human-readable game name")
    args = parser.parse_args()

    run_pipeline(args.urls, args.output, args.game)

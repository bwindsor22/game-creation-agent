"""
youtube_pipeline.py — Download YouTube videos, extract frames + transcripts,
caption frames with Claude vision, and generate structured game guidelines.

Usage:
    python3 tools/youtube_pipeline.py URL [URL ...] --output /path/to/output/dir
    python3 tools/youtube_pipeline.py URL --output /path --game "Game Name"

Output (in --output dir):
    captioned_videos.json   — per-frame base64 images + captions
    guidelines.md           — structured game guidelines for testing

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

def download_video(url: str, out_dir: str) -> str:
    """Download a YouTube video as MP4. Returns path to the downloaded file."""
    output_template = os.path.join(out_dir, "%(id)s.%(ext)s")
    subprocess.run(
        [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url,
        ],
        check=True,
    )
    files = list(Path(out_dir).glob("*.mp4"))
    if not files:
        raise RuntimeError(f"No MP4 found after downloading {url}")
    return str(sorted(files)[0])


# ---------------------------------------------------------------------------
# Step 2: Extract frames with ffmpeg (no opencv needed)
# ---------------------------------------------------------------------------

def extract_frames(video_path: str, frame_dir: str, interval: int = FRAME_INTERVAL_SECONDS) -> list[tuple[float, str]]:
    """Extract one frame every `interval` seconds. Returns list of (timestamp_s, image_path)."""
    os.makedirs(frame_dir, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
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

def generate_guidelines(
    client: anthropic.Anthropic,
    game_name: str,
    transcript_text: str,
    frames: list[tuple[float, str]],
    output_path: str,
) -> str:
    """Synthesize a structured game guidelines markdown document for testing."""
    # Sample up to 6 evenly-spaced frames for context
    step = max(1, len(frames) // 6)
    sampled = frames[::step][:6]

    content: list = []
    for ts, img_path in sampled:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": encode_image(img_path)},
        })
    content.append({
        "type": "text",
        "text": (
            f"You are a game implementation expert. The images above are frames from a "
            f"'{game_name}' how-to-play tutorial video. Below is the full transcript:\n\n"
            f"{transcript_text[:12000]}\n\n"
            "Produce a structured markdown document titled '# {game_name} — Play Guidelines'.\n"
            "Include these sections:\n"
            "## Setup — board layout, piece placement, starting conditions\n"
            "## Turn Structure — exactly what a player does on their turn, in order\n"
            "## Valid Moves — precise conditions for each move type\n"
            "## Win Condition — how the game ends and who wins\n"
            "## Key Rules — any special rules, edge cases, or common mistakes\n"
            "## Testing Checklist — a bulleted list of game states / scenarios that a "
            "QA tester should verify in a digital implementation\n\n"
            "Be precise enough that a programmer can write automated tests from this document."
        ).format(game_name=game_name),
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

def process_video(url: str, work_dir: str, game_name: str, client: anthropic.Anthropic) -> dict:
    """Full pipeline for one video URL. Returns the JSON result dict."""
    print(f"\n=== {url} ===")

    video_dir = os.path.join(work_dir, "video")
    frame_dir = os.path.join(work_dir, "frames")
    os.makedirs(video_dir, exist_ok=True)

    print("  Downloading...")
    video_path = download_video(url, video_dir)

    print("  Extracting frames...")
    frames = extract_frames(video_path, frame_dir)
    print(f"  {len(frames)} frames extracted")

    print("  Transcribing with Whisper...")
    segments = transcribe(video_path)
    print(f"  {len(segments)} transcript segments")

    print("  Captioning frames with Claude...")
    captioned_images = []
    for i, (ts, img_path) in enumerate(frames):
        print(f"    Frame {i+1}/{len(frames)} @ {ts:.0f}s")
        window = transcript_window(segments, ts)
        b64 = encode_image(img_path)
        caption = caption_frame(client, b64, window) if window else "(no transcript)"
        captioned_images.append({
            "timestamp_s": ts,
            "image_encoded": b64,
            "transcription": caption,
        })

    return {
        "link": url,
        "game": game_name,
        "segments": [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in segments],
        "captioned_images": captioned_images,
        "_frames": frames,  # internal; removed before JSON serialisation
        "_full_transcript": full_transcript(segments),
    }


def run_pipeline(urls: list[str], output_dir: str, game_name: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    client = anthropic.Anthropic()

    results = []
    for url in urls:
        with tempfile.TemporaryDirectory() as work_dir:
            data = process_video(url, work_dir, game_name, client)

            # Generate guidelines while frames are still on disk
            guidelines_path = os.path.join(output_dir, "guidelines.md")
            print("  Generating game guidelines...")
            generate_guidelines(client, game_name, data["_full_transcript"], data["_frames"], guidelines_path)
            print(f"  Guidelines saved to {guidelines_path}")

            # Strip internal keys before saving JSON
            clean = {k: v for k, v in data.items() if not k.startswith("_")}
            results.append(clean)

    json_path = os.path.join(output_dir, "captioned_videos.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nJSON saved to {json_path}")
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube → captioned frames + game guidelines")
    parser.add_argument("urls", nargs="+", help="YouTube URLs to process")
    parser.add_argument("--output", required=True, help="Directory to write output files")
    parser.add_argument("--game", default="Unknown Game", help="Human-readable game name")
    args = parser.parse_args()

    run_pipeline(args.urls, args.output, args.game)

# YouTube Pipeline — Status & Notes

## Pipeline

Tool: `tools/youtube_pipeline.py`

### Steps
1. Try to download video with `yt-dlp` (falls back gracefully if blocked)
2. Extract frames at 30s intervals with `ffmpeg`
3. Transcribe audio with Whisper `small` model — OR fall back to `youtube-transcript-api`
4. Caption each frame with Claude vision (only if frames downloaded)
5. Generate structured `guidelines.md` from transcript + frames

### Dependencies
- `yt-dlp` — installed at `~/.pyenv/shims/yt-dlp` (pyenv 3.12, v2026.3.3). Update with: `PYENV_VERSION=3.12.2 pip install -U yt-dlp`
- `ffmpeg` — `/opt/homebrew/bin/ffmpeg`
- `openai-whisper` — installed in system python 3.9
- `youtube-transcript-api` — installed in system python 3.9 (fallback)
- `anthropic` SDK — installed

Run with pyenv 3.12 (has latest yt-dlp): `PYENV_VERSION=3.12.2 python3 tools/youtube_pipeline.py URL --output /path --game "Name"`

Or with system python (uses pyenv 3.12's yt-dlp automatically via path discovery): `/usr/bin/python3 tools/youtube_pipeline.py URL --output /path --game "Name"`

---

## Processed Videos

| Video | Game | Status | Output |
|-------|------|--------|--------|
| [FxW9Nk8139o](https://www.youtube.com/watch?v=FxW9Nk8139o) | stacks-game (Tak) | ✅ transcript (298 segments) + 24 frames + guidelines.md | `/code/stacks-game/resources/youtube/FxW9Nk8139o/` |

---

## Notes

- YouTube sometimes blocks video download (HTTP 403 bot detection). Pipeline falls back to `youtube-transcript-api` for transcript-only mode (no frames/captions).
- Whisper `small` model works well for board game tutorials. `base` is faster but less accurate.
- `guidelines.md` output is designed to be a QA testing document, not implementation instructions.
- Frame captioning requires the video download to succeed — skipped in transcript-only mode.

### Fixing 403 / bot detection errors (in order of reliability)
1. **Update yt-dlp first** — stale versions are the #1 cause: `PYENV_VERSION=3.12.2 pip install -U yt-dlp`
2. **Android player client** — bypasses SABR streaming: `--extractor-args youtube:player_client=android`
3. **Browser cookies** — `--cookies-from-browser chrome` or `safari`
4. **Format selection** — `bv*+ba/b` requests separate streams (less blocked than combined)
5. **Throttle** — `--sleep-interval 2` avoids rate-limit triggers

The updated `download_video()` function tries these strategies in order automatically.

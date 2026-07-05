# Reel → Transcript

Status: candidate

## Goal

Find (or build) an easy way to turn an Instagram reel into a text transcript.

First candidate reel: https://www.instagram.com/reel/DaZE28Wg6RQ/

## Research notes (2026-07)

### Option A — DIY pipeline: yt-dlp + Whisper

The standard local approach: download the reel's audio with `yt-dlp`, transcribe with Whisper.

- [ReelStudio](https://github.com/stym06/reelstudio) is an open-source reference implementation of exactly this (paste URL → yt-dlp download → Whisper transcript). Good to study or self-host.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2-based) is ~4x faster than vanilla Whisper at the same accuracy — prefer it for local runs.
- **Big caveat:** Instagram disabled most anonymous reel-download endpoints in late 2024. `yt-dlp` needs authentication — pass logged-in browser cookies via `--cookies-from-browser firefox` (or `--cookies cookies.txt`). See [yt-dlp#11151](https://github.com/yt-dlp/yt-dlp/issues/11151).

Sketch (untested — needs a machine with an Instagram-logged-in browser):

```bash
yt-dlp --cookies-from-browser firefox -x --audio-format mp3 \
  -o reel.mp3 "https://www.instagram.com/reel/DaZE28Wg6RQ/"
pip install faster-whisper
python -c "
from faster_whisper import WhisperModel
segments, _ = WhisperModel('small').transcribe('reel.mp3')
print(' '.join(s.text for s in segments))
"
```

### Option B — Hosted paste-a-link tools

Zero setup: paste the reel URL, get text back. Trade-offs are rate limits, accounts, and sending content to a third party.

- [GetTheScript](https://getthescript.app/instagram-transcript) — free, no signup claimed
- [WayinVideo](https://wayin.ai/tools/video-transcript-generator/instagram/) — free tier, exports TXT/SRT/VTT, ~60 min/day after signup
- [SpeakApp](https://speakapp.com/t/tools/instagram-transcript) — works from public reel URLs, 50+ languages
- [ScreenApp](https://screenapp.io/transcription/instagram), [Speak AI](https://speakai.co/transcribe/instagram/) — similar

### Constraints observed

- Instagram returns 403 to unauthenticated server-side fetches (confirmed from this environment), so any automated solution needs either authenticated cookies (Option A) or a hosted service that maintains its own access (Option B).

## Recommendation

- For a quick one-off on this candidate reel: try a hosted tool (Option B) first.
- For a repeatable tool we own: build on Option A — yt-dlp with browser cookies + faster-whisper, using ReelStudio as the reference.

## Next steps

- [ ] Run the candidate reel through a hosted tool to get a baseline transcript
- [ ] Test the yt-dlp cookie flow from a machine logged into Instagram
- [ ] If both work, decide whether to wrap the DIY pipeline into a small CLI in this lane

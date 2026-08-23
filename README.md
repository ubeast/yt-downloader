# yt-downloader

Download a single YouTube video at its highest available resolution.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) on `PATH` (`brew install ffmpeg`) — required to
  merge the separate video and audio streams YouTube serves for 1080p and
  above. Without it, downloads silently cap out around 720p.

## Install

```bash
uv sync
```

## Usage

```bash
uv run yt-downloader "https://www.youtube.com/watch?v=VIDEO_ID"

# custom output directory
uv run yt-downloader "https://www.youtube.com/watch?v=VIDEO_ID" -o ~/Downloads
```

By default, videos are saved to `downloads/` in this repo (created if it
doesn't exist), regardless of where you run the command from. Pass `-o` to
override.

## How it works

Built on [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) rather than `pytube`,
since `pytube` parses YouTube's frontend directly and breaks frequently as
YouTube changes it; `yt-dlp` is actively maintained against those changes.

Requests `bestvideo+bestaudio`, which selects the highest-resolution
video-only stream and the best audio-only stream, then muxes them into an
`.mp4` via ffmpeg.

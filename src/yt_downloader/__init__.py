"""yt-downloader: download a YouTube video at its highest available resolution.

Follow-on developer notes
--------------------------
This wraps `yt-dlp` (https://github.com/yt-dlp/yt-dlp), not the older `pytube`
library. `pytube` parses YouTube's page/player JS directly and breaks every
time YouTube changes its frontend; `yt-dlp` is actively maintained against
those changes and is the de facto standard for this task, so we trade a
slightly heavier dependency for reliability.

Resolution note: YouTube usually serves its highest-resolution formats
(1080p and above) as separate video-only and audio-only streams (DASH),
not as a single progressive file. To get "highest resolution" you must
download both and mux them together, which requires `ffmpeg` on PATH.
Without ffmpeg, yt-dlp silently falls back to the best progressive
(video+audio combined) format, which caps out around 720p.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yt_dlp


class FfmpegNotFoundError(RuntimeError):
    """Raised when ffmpeg is required to merge streams but isn't on PATH."""


# Resolves to the repo root (src/yt_downloader/__init__.py -> yt_downloader ->
# src -> repo root), so downloads always land in the same place regardless of
# the caller's working directory. Only correct when running from a checkout
# (e.g. via `uv run`); an installed wheel would resolve this into
# site-packages, so this default assumes the "run from this repo" workflow.
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "downloads"


def download_highest_resolution(
    url: str,
    output_dir: Path,
    *,
    filename_template: str = "%(title)s [%(id)s].%(ext)s",
) -> Path:
    """Download a single YouTube video at its highest available resolution.

    Args:
        url: Full YouTube video URL (or any URL yt-dlp's extractors support).
        output_dir: Directory to save the downloaded file into. Created if
            it doesn't exist.
        filename_template: yt-dlp output template for the saved filename.
            Defaults to "Title [video_id].ext" to avoid collisions between
            videos that share a title.

    Returns:
        Path to the downloaded (and, if needed, muxed) file on disk.

    Raises:
        FfmpegNotFoundError: if ffmpeg is missing, since the highest-res
            formats are usually split video/audio streams that must be
            merged.
        yt_dlp.utils.DownloadError: on network failures, invalid/private
            URLs, or age/region-restricted content yt-dlp can't bypass.

    Performance note: this blocks until the download finishes and shells
    out to ffmpeg for remuxing, which briefly duplicates disk usage
    (separate video/audio parts, then the merged file) before yt-dlp
    cleans up the intermediates.
    """
    if shutil.which("ffmpeg") is None:
        raise FfmpegNotFoundError(
            "ffmpeg is required to merge the highest-resolution video and "
            "audio streams. Install it (e.g. `brew install ffmpeg`) and "
            "retry."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts: dict[str, object] = {
        # bestvideo+bestaudio picks the highest-res video stream and best
        # audio stream separately and muxes them; the fallback keeps this
        # working even if no split streams are available for a given video.
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": str(output_dir / filename_template),
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info)).with_suffix(".mp4")


def main() -> None:
    """CLI entry point: `yt-downloader <url> [-o output_dir]`."""
    parser = argparse.ArgumentParser(
        description="Download a YouTube video at its highest available resolution."
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to save the video into (default: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()

    try:
        output_path = download_highest_resolution(args.url, args.output_dir)
    except FfmpegNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except yt_dlp.utils.DownloadError as exc:
        print(f"error: download failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()

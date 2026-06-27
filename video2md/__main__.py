from __future__ import annotations

import argparse
import os
from pathlib import Path

from .pipeline import PipelineConfig, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="video2md",
        description="Download or read a video/audio source, transcribe it, summarize it, and write a Markdown note.",
    )
    parser.add_argument("source", help="A video URL, local media file, or source label when --transcript-file is used.")
    parser.add_argument("--title", help="Markdown note title. Defaults to the URL/file name.")
    parser.add_argument("--output-dir", default="knowledge", help="Directory for generated Markdown notes.")
    parser.add_argument("--work-dir", default=".video2md-work", help="Directory for intermediate files.")
    parser.add_argument(
        "--download-command",
        default=os.getenv("VIDEO2MD_DOWNLOAD_COMMAND"),
        help="Command template for URL download. Placeholders: {url}, {video}.",
    )
    parser.add_argument(
        "--extract-command",
        default=os.getenv("VIDEO2MD_EXTRACT_COMMAND", "ffmpeg -y -i {video} -vn -ac 1 -ar 16000 {audio}"),
        help="Command template for audio extraction. Placeholders: {video}, {audio}.",
    )
    parser.add_argument(
        "--transcribe-command",
        default=os.getenv("VIDEO2MD_TRANSCRIBE_COMMAND"),
        help="Command template for ASR. Placeholders: {audio}, {transcript}.",
    )
    parser.add_argument(
        "--summarize-command",
        default=os.getenv("VIDEO2MD_SUMMARIZE_COMMAND"),
        help="Optional command template for LLM summary. Placeholders: {transcript}, {summary}.",
    )
    parser.add_argument(
        "--transcript-file",
        type=Path,
        help="Use an existing transcript text file and skip download/audio/transcription steps.",
    )
    parser.add_argument("--clean-work", action="store_true", help="Delete intermediate files after writing the note.")

    args = parser.parse_args()
    result = run_pipeline(
        source=args.source,
        config=PipelineConfig(
            output_dir=Path(args.output_dir),
            work_dir=Path(args.work_dir),
            title=args.title,
            download_command=args.download_command,
            extract_command=args.extract_command,
            transcribe_command=args.transcribe_command,
            summarize_command=args.summarize_command,
            transcript_file=args.transcript_file,
            keep_work=not args.clean_work,
        ),
    )
    print(result.note_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

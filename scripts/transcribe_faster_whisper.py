from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe audio with faster-whisper.")
    parser.add_argument("audio", type=Path)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--model", default="small")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="auto")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit("Missing dependency: install faster-whisper before using this script.") from exc

    kwargs = {}
    if args.compute_type != "default":
        kwargs["compute_type"] = args.compute_type
    model = WhisperModel(args.model, device=args.device, **kwargs)
    language = None if args.language == "auto" else args.language
    segments, _ = model.transcribe(str(args.audio), language=language, vad_filter=True)
    text = "\n".join(segment.text.strip() for segment in segments if segment.text.strip())

    args.transcript.parent.mkdir(parents=True, exist_ok=True)
    args.transcript.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

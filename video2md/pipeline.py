from __future__ import annotations

import datetime as dt
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from string import Formatter
from urllib.parse import urlparse


Runner = callable


@dataclass(frozen=True)
class PipelineConfig:
    output_dir: Path
    work_dir: Path
    title: str | None = None
    download_command: str | None = None
    extract_command: str = "ffmpeg -y -i {video} -vn -ac 1 -ar 16000 {audio}"
    transcribe_command: str | None = None
    summarize_command: str | None = None
    transcript_file: Path | None = None
    keep_work: bool = True


@dataclass(frozen=True)
class PipelineResult:
    note_path: Path
    transcript_path: Path
    summary_path: Path | None
    work_dir: Path


def default_runner(command: str) -> None:
    subprocess.run(command, shell=True, check=True)


def run_pipeline(source: str, config: PipelineConfig, runner=default_runner) -> PipelineResult:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.work_dir.mkdir(parents=True, exist_ok=True)

    title = config.title or _title_from_source(source)
    video_path = config.work_dir / "source.mp4"
    audio_path = config.work_dir / "audio.wav"
    transcript_path = config.work_dir / "transcript.txt"
    summary_path = config.work_dir / "summary.md"

    if config.transcript_file:
        transcript_path.write_text(
            Path(config.transcript_file).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    else:
        if _is_url(source):
            if not config.download_command:
                raise ValueError("URL input requires --download-command or VIDEO2MD_DOWNLOAD_COMMAND.")
            _run_template(runner, config.download_command, url=source, video=video_path)
        else:
            source_path = Path(source)
            if not source_path.exists():
                raise FileNotFoundError(source)
            shutil.copyfile(source_path, video_path)

        _run_template(runner, config.extract_command, video=video_path, audio=audio_path)

        if not config.transcribe_command:
            raise ValueError("Transcription requires --transcribe-command or --transcript-file.")
        _run_template(
            runner,
            config.transcribe_command,
            audio=audio_path,
            transcript=transcript_path,
        )

    summary_for_note = None
    if config.summarize_command:
        _run_template(
            runner,
            config.summarize_command,
            transcript=transcript_path,
            summary=summary_path,
        )
        summary_for_note = summary_path.read_text(encoding="utf-8") if summary_path.exists() else None

    note_path = config.output_dir / f"{_slugify(title)}.md"
    note_path.write_text(
        _render_note(
            title=title,
            source=source,
            transcript=transcript_path.read_text(encoding="utf-8"),
            summary=summary_for_note,
        ),
        encoding="utf-8",
    )

    if not config.keep_work:
        shutil.rmtree(config.work_dir)

    return PipelineResult(
        note_path=note_path,
        transcript_path=transcript_path,
        summary_path=summary_path if summary_for_note is not None else None,
        work_dir=config.work_dir,
    )


def _run_template(runner, template: str, **values: Path | str) -> None:
    command = _format_command(template, values)
    runner(command)


def _format_command(template: str, values: dict[str, Path | str]) -> str:
    fields = {name for _, name, _, _ in Formatter().parse(template) if name}
    missing = fields - values.keys()
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"Command template has unknown placeholder(s): {names}")
    return template.format(**{key: str(value) for key, value in values.items()})


def _render_note(title: str, source: str, transcript: str, summary: str | None) -> str:
    created_at = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    parts = [
        f"# {title}",
        "",
        f"- Source: {source}",
        f"- Created: {created_at}",
        "",
    ]
    if summary:
        parts.extend([summary.strip(), ""])
    parts.extend(["## 转写", "", transcript.strip(), ""])
    return "\n".join(parts)


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _title_from_source(source: str) -> str:
    if _is_url(source):
        path = urlparse(source).path.rstrip("/")
        return Path(path).name or urlparse(source).netloc
    return Path(source).stem


def _slugify(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value).strip(" .-")
    return cleaned or "video-note"

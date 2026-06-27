from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from video2md.cookies import inspect_cookie_header
from video2md.pipeline import PipelineConfig, run_pipeline


DEFAULT_TITLE = "抖音视频笔记"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Douyin -> audio -> transcript -> Markdown workflow.")
    parser.add_argument("url")
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--cookie-file", type=Path, default=Path("cookies.txt"))
    parser.add_argument("--douk-dir", type=Path, default=Path("C:/tmp/video2md-run/DouK-Downloader"))
    parser.add_argument("--run-dir", type=Path, default=Path("runs/douyin"))
    parser.add_argument("--output-dir", type=Path, default=Path("knowledge"))
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--douk-pythonpath", default=os.getenv("VIDEO2MD_DOUK_PYTHONPATH", ""))
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--transcribe-command", required=True)
    parser.add_argument("--summarize-command")
    args = parser.parse_args()

    cookie = _read_cookie(args.cookie_file)
    _check_cookie(cookie)
    _check_douk_dir(args.douk_dir)

    args.run_dir.mkdir(parents=True, exist_ok=True)
    source_video = args.run_dir / "source.mp4"
    audio = args.run_dir / "audio.wav"
    transcript = args.run_dir / "transcript.txt"

    output_root = args.run_dir / "douk-output"
    before = set(_media_files(output_root))
    _run_douk(args.douk_dir, args.python, args.douk_pythonpath, cookie, args.url, output_root)
    video = _newest_video(output_root, before)
    shutil.copyfile(video, source_video)

    _run([args.ffmpeg, "-y", "-i", str(source_video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    _run_template(args.transcribe_command, audio=audio, transcript=transcript)

    result = run_pipeline(
        source=args.url,
        config=PipelineConfig(
            output_dir=args.output_dir,
            work_dir=args.run_dir / "work",
            title=args.title,
            transcript_file=transcript,
            summarize_command=args.summarize_command,
        ),
    )
    print(result.note_path)
    return 0


def _read_cookie(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Cookie file not found: {path}")
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        raise SystemExit(f"Cookie file is empty: {path}")
    return text


def _check_cookie(text: str) -> None:
    report = inspect_cookie_header(text)
    missing = []
    if not report.has_session_cookie:
        missing.append("sessionid/sid_guard")
    if not report.has_odin_tt:
        missing.append("odin_tt")
    if not report.has_ttwid:
        missing.append("ttwid")
    if missing:
        names = ", ".join(missing)
        raise SystemExit(f"Cookie file is missing likely Douyin cookie(s): {names}")
    print(f"cookie check ok: {report.count} names")


def _check_douk_dir(path: Path) -> None:
    if not path.joinpath("main.py").exists() or not path.joinpath("Volume", "settings.json").exists():
        raise SystemExit(
            "DouK-Downloader not found or not initialized. "
            "Clone it and run it once, then pass --douk-dir."
        )


def _run_douk(
    douk_dir: Path,
    python: str,
    douk_pythonpath: str,
    cookie: str,
    url: str,
    output_root: Path,
) -> None:
    settings = douk_dir / "Volume" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8-sig"))
    old_cookie = data.get("cookie", "")
    try:
        data["cookie"] = cookie.split(":", 1)[1].strip() if cookie.lower().startswith("cookie:") else cookie
        data["root"] = str(output_root)
        data["folder_name"] = "Download"
        data["download"] = True
        data["storage_format"] = ""
        settings.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
        command = f"5\n2\n1\n{url}\n\nQ\n"
        env = os.environ.copy()
        if douk_pythonpath:
            env["PYTHONPATH"] = douk_pythonpath + os.pathsep + env.get("PYTHONPATH", "")
        subprocess.run(
            [python, "main.py"],
            cwd=douk_dir,
            env=env,
            input=command,
            text=True,
            check=True,
        )
    finally:
        try:
            data["cookie"] = old_cookie
            settings.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
        except Exception:
            pass


def _media_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.suffix.lower() in {".mp4", ".webm", ".m4a"}]


def _newest_video(root: Path, before: set[Path]) -> Path:
    candidates = [p for p in _media_files(root) if p not in before and p.suffix.lower() == ".mp4"]
    if not candidates:
        candidates = [p for p in _media_files(root) if p.suffix.lower() == ".mp4"]
    if not candidates:
        raise SystemExit(f"No downloaded mp4 found under {root}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _run_template(template: str, **values: Path) -> None:
    command = template.format(**{key: str(value) for key, value in values.items()})
    subprocess.run(command, shell=True, check=True)


if __name__ == "__main__":
    raise SystemExit(main())

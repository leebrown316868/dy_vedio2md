---
name: capturing-douyin-video-notes
description: Use when a user wants to turn Douyin video URLs into local Markdown notes from a fresh Windows or agent environment, especially when cookies, Git/Python/FFmpeg/DouK/faster-whisper setup, CUDA errors, artifact locations, or AI-written summaries are involved.
---

# Capturing Douyin Video Notes

## Overview

This skill turns a Douyin URL into a local Markdown knowledge note. The user provides intent, approvals, and local cookies; the agent sets up tools, downloads, transcribes on CPU, summarizes with the current AI, renames the note from content, and reports every process/output location.

## Non-Negotiable Rules

- Cookie-first: Douyin requires cookies. Do not waste a no-cookie attempt. Ask for a local cookie file path before download.
- Approval UX: do not ask the user to type `y`, `yes`, `1`, or any confirmation text. Any consent must be requested through the agent's ask/approval mechanism.
- Current-AI summary: after ASR creates `transcript.txt`, the AI currently executing this skill reads it and writes the summary. Do not default to Ollama/local LLM.
- CPU transcription: faster-whisper must run with `--device cpu --compute-type int8` unless the user explicitly requests GPU and confirms CUDA works.
- Content filename: do not leave the final note named only as an id. Derive a short title from the AI analysis, sanitize it, rename the Markdown file, and report the final path.
- Completion report: always tell the user where process files, installed dependencies, caches, transcript, audio, video, cookies, and final notes are located.

## First Response

Say this, adjusted to the actual user request:

> I can set up the open-source tools, download the Douyin video with your local cookies, extract audio, transcribe on CPU, summarize it myself, and save a renamed Markdown note. I will ask for approvals through the agent UI, not by making you type confirmations. At the end I will report where all process files and outputs were written.

Collect only:

1. Douyin URL.
2. Local cookie file path, such as `<workspace>\cookies.txt`. Do not ask the user to paste cookie values.
3. Workspace path, or suggest a neutral default such as `%USERPROFILE%\dy_vedio2md`.
4. Knowledge output directory, or default to `<workspace>\knowledge`.
5. Agent approvals for network installs, browser access, closing browser, or GUI/manual initialization.

## Bootstrap Order

1. Locate or clone `https://github.com/leebrown316868/dy_vedio2md.git` into `<workspace>`.
2. Locate Git Bash, Python 3.10+, FFmpeg, and the project scripts. Use discovered absolute paths.
3. Choose `<tool-cache>`, preferably `%LOCALAPPDATA%\video2md-run` on Windows.
4. Prepare DouK/TikTokDownloader in `<tool-cache>\DouK-Downloader`; dependency installs go under `<tool-cache>\douk-deps`.
5. Prepare faster-whisper dependencies under `<tool-cache>\asr-deps`; model/cache files go under `<tool-cache>\hf-cache`.
6. Verify cookie file exists, is non-empty, and contains likely Douyin cookie names. Print names/count only, never values.
7. Run download with absolute `--run-dir`, `--output-dir`, `--douk-dir`, and `--cookie-file`.
8. Run transcription on CPU:

```bash
--transcribe-pythonpath "<tool-cache>/asr-deps"
--transcribe-env "HF_HOME=<tool-cache>/hf-cache"
--transcribe-command '<python> scripts/transcribe_faster_whisper.py "{audio}" "{transcript}" --model base --device cpu --compute-type int8 --language auto'
```

9. Read `transcript.txt`, summarize with the current AI, write/update Markdown.
10. Rename the Markdown file using a content-derived title.
11. Give the completion report.

## Why CUDA Errors Happen

`cublas64_12.dll` errors happen when faster-whisper/CTranslate2 tries CUDA but the machine lacks compatible CUDA runtime DLLs. Avoid this for zero-base users by always passing `--device cpu --compute-type int8`. Do not let `device=auto` decide.

## Completion Report

End every successful run with a compact report:

| Item | Path |
| --- | --- |
| Workspace/repo | `<workspace>` |
| Tool cache | `<tool-cache>` |
| DouK program | `<tool-cache>\DouK-Downloader` |
| DouK deps | `<tool-cache>\douk-deps` |
| ASR deps | `<tool-cache>\asr-deps` |
| ASR/model cache | `<tool-cache>\hf-cache` |
| Cookie file | `<cookie-file>` (values not shown) |
| Run dir | `<workspace>\runs\<id>` |
| Source video | `<run-dir>\source.mp4` |
| Audio | `<run-dir>\audio.wav` |
| Transcript | `<run-dir>\transcript.txt` |
| Final note | `<knowledge>\<content-title>.md` |

Also state what was cleaned, for example temporary DouK cookie settings restored. If files remain intentionally, say so; do not delete user artifacts unless explicitly asked.

## Filename Rule

After summarizing, infer a concise Chinese title from the actual content, not from the Douyin id. Sanitize it for Windows filenames:

- Remove `<>:"/\|?*` and control characters.
- Keep it under about 60 characters.
- If the title collides, append `-2`, `-3`, etc.
- Rename the Markdown note to `<title>.md`.
- The final user-facing sentence must use the content title path, not `knowledge\<video-id>.md`.

## Approval Rules

- Use the agent's ask/approval mechanism for installs, browser access, process closing, and visible/manual GUI steps.
- Do not write prompts like "please type yes" or "enter 1 to confirm".
- If a CLI requires interactive confirmation, first obtain agent approval, then automate the CLI input yourself when safe. For account/security actions, stop and use agent ask.

## DouK Rules

- DouK must be initialized before automation. If `Volume/settings.json` is missing, ask through agent approval before visible/manual initialization.
- Use absolute paths for `run-dir`, `output-dir`, and DouK `root`.
- Restore/clear temporary DouK cookie settings after the run.
- If target run dir has no MP4, search `DouK-Downloader/Volume/Download/**/*.mp4`, copy the newest matching file to `<run-dir>\source.mp4`, and resume from FFmpeg.
- If menu piping fails, do not repeat the same sequence. Check initialization, paths, and default download dir, then ask for approval before any manual/visible fallback.

## Red Flags

- Trying Douyin download without cookies.
- Asking the user to paste cookies into chat.
- Asking the user to type confirmation text instead of using agent ask.
- Printing cookie values or request headers.
- Running faster-whisper with `device=auto` or without `--device cpu --compute-type int8`.
- Leaving final note named as a raw video id.
- Saying only "saved to ..." without reporting process file locations.
- Assuming Git Bash has `python` or that paths match the developer's machine.

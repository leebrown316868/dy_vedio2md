---
name: capturing-douyin-video-notes
description: Use when a user wants to turn Douyin video URLs into local Markdown notes, especially from a fresh Windows/Codex environment with missing repo, downloaders, FFmpeg, ASR, cookies, or shell setup.
---

# Capturing Douyin Video Notes

## Overview

This skill is the runbook for going from "I only have a Douyin URL" to a local Markdown knowledge note. Treat the human as the source of intent and authorization; let Codex/programs handle environment setup, open-source tool installation, download, transcription, and verification. The current AI assistant performs the final summarization unless the user explicitly chooses another summarizer.

## First Response

Say the boundary clearly:

> I can set up the repo and open-source tools, then run download, audio extraction, transcription, and Markdown output. After transcription, I will summarize the content myself in this chat/session unless you explicitly ask to use a local LLM. You only need to provide the video URL, approve installs or browser access when needed, and provide a local cookie file if Douyin requires login. I will not print cookie values.

Collect only missing inputs:

1. Douyin URL.
2. Workspace path. If the user does not know, suggest a neutral default such as `%USERPROFILE%\dy_vedio2md` on Windows.
3. Permission before network installs, Git clone, browser-cookie access, or closing Edge/Chrome.
4. Cookie file path only after no-cookie download fails.
5. Knowledge output directory, or default to `<workspace>\knowledge`.

## Zero-Environment Bootstrap

Use this order for a fresh Windows user:

1. Locate Git Bash. Search common Git for Windows locations, then ask permission to install Git if it is missing. Do not assume the user's Git Bash path.
2. Clone the project if missing:
   `git clone https://github.com/leebrown316868/dy_vedio2md.git <workspace>`.
3. Use an absolute Python path. In Codex Desktop, prefer workspace dependency Python; otherwise locate `py`, `python`, or ask permission to install Python 3.10+.
4. Install project package only if needed: `python -m pip install -e <workspace>`.
5. Choose a tool cache directory such as `%LOCALAPPDATA%\video2md-run` on Windows. Prepare DouK/TikTokDownloader under `<tool-cache>\DouK-Downloader`; clone it if missing and install dependencies into `<tool-cache>\douk-deps`.
6. Locate FFmpeg. If missing, ask permission to install with WinGet or another local package manager.
7. Prepare ASR dependencies under `<tool-cache>\asr-deps`; default to faster-whisper CPU `base` or `small`, `int8`.
8. Run one unauthenticated download attempt. Do not pass `--cookie-file` yet. If it fails, ask the human to save Douyin `Cookie` to a local `cookies.txt`, then retry with `--cookie-file <cookie-file>`.
9. Run the pipeline with absolute `--run-dir` and `--output-dir`.
10. Read `transcript.txt` and summarize with the current AI assistant. Do not default to Ollama or any local LLM.
11. Verify `source.mp4`, `audio.wav`, `transcript.txt`, and the final Markdown note exist.

## Windows Command Rules

Assume two parsers: PowerShell first, then Bash/Python.

- For human-facing PowerShell commands, prefer stop-parsing:

```powershell
& '<path-to-git-bash>\bash.exe' --% -lc "cd '<workspace-as-bash-path>' && ..."
```

- Inside Codex shell tools, still start every command with the discovered Git Bash executable.
- Do not assume `python` exists in Git Bash; use absolute paths.
- Avoid inline Python, here-docs, and long templates inside one shell line.
- Avoid spaces in operational `--title`; use the video id first, then edit the Markdown title later.
- Do not put `set PYTHONPATH=...&&`, `export PYTHONPATH=...`, or other shell-specific environment syntax inside `--transcribe-command`. Use `--transcribe-pythonpath <path>` and `--transcribe-env KEY=VALUE`.
- Prefer command files or wrapper scripts over complex `--transcribe-command` strings.
- Use concrete paths only after discovering them on the user's machine. In user-facing prompts, say `<workspace>`, `<tool-cache>`, or `<cookie-file>` until the actual path is known.

## Human vs Program

| Step | Human provides | Codex/program does |
| --- | --- | --- |
| Source | Video URL and goal | Clone repo, create run directory |
| Installs | Approval for network/package actions | Install open-source tools locally |
| Auth | Cookie file or browser-cookie permission | Use cookies without printing values |
| Browser lock | Permission before closing browser | Retry cookie read after approval |
| Download | Nothing after auth is valid | Use DouK first, yt-dlp only as fallback |
| Transcription | Language/model preference if desired | Extract audio and run ASR |
| Summary | Focus/style judgment | Current AI reads transcript and writes the summary |
| Verification | Final usefulness judgment | Check files and report paths |

## Cookie Handling

If no-cookie download fails, guide the user to DevTools `Network` -> a real Douyin request -> `Headers` -> `Request Headers` -> `Cookie`. If they show `Payload`, redirect them to `Headers`.

Never ask the user to paste secrets into chat. Ask them to save a local file such as `cookies.txt`. Inspect only existence, size, and cookie names; never print values.

## DouK Rules

- Use absolute paths for `run-dir`, `output-dir`, and DouK `root`, such as `<workspace>/runs/<id>` after resolving `<workspace>` on the user's machine.
- DouK must be initialized before automation. If `Volume/settings.json` is missing, run DouK once interactively to select language and accept its disclaimer, then retry.
- Clean temporary DouK settings that contain cookie values.
- If DouK says the item already exists but the requested run dir has no MP4, search `DouK-Downloader/Volume/Download/**/*.mp4`, copy the newest matching file to `<run-dir>/source.mp4`, and resume from FFmpeg.
- If piped/menu input into DouK fails, do not keep sending the same menu sequence. Verify initialization, use absolute output paths, check DouK's default download directory, then ask the human before switching to a visible/manual DouK initialization step.

## Summary Rule

The summarizer is "you": the AI currently executing this skill. After ASR produces `transcript.txt`, read the transcript and write the Markdown summary directly.

Do not assume the user has Ollama, a local model, or `scripts/summarize_ollama.py`. Use a local summarizer only when the user explicitly requests it or the current environment requires fully offline summarization.

## Open-Source User Flow

When the repo is public, guide a beginner like this:

1. "Install/use this skill in Codex."
2. "Give me the Douyin URL."
3. Codex clones `leebrown316868/dy_vedio2md`, installs open-source dependencies with approval, and checks paths on that user's machine.
4. Human logs into Douyin and saves `cookies.txt` only if needed.
5. Codex runs the pipeline, reads the transcript, summarizes it itself, writes Markdown, and reports local artifact paths.

The human should not need to know DouK, FFmpeg, ASR, shell quoting, or Python path details.

## Program Improvements To Prefer

When editing the project, prioritize:

- Resolve all downloader paths to absolute paths.
- Fallback-search DouK default downloads when target dir is empty.
- Keep `--cookie-file` optional so the first attempt can run without Cookie.
- Add `--transcribe-command-file` or env defaults.
- Add `--title-file` or default operational title to video id.
- Print parsed paths and argument diagnostics, never secrets.

## Red Flags

- Retrying the same downloader command without new auth.
- Treating `blob:` as a source MP4.
- Printing cookie values or request headers.
- Asking the user to paste cookies into chat.
- Closing a browser without explicit permission.
- Passing relative paths to DouK.
- Debugging argparse before checking PowerShell splitting.
- Assuming Git Bash has `python`.
- Encoding PYTHONPATH inside the transcribe shell command.
- Requiring Cookie before trying the no-cookie path.

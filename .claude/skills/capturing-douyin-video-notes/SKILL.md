---
name: capturing-douyin-video-notes
description: Use when a user wants to turn Douyin or Bilibili (B站) video URLs into local Markdown notes from a fresh Windows or agent environment, especially when cookies, Git/Python/FFmpeg/DouK/yt-dlp/faster-whisper setup, CUDA errors, artifact locations, or AI-written summaries are involved.
---

# Capturing Video Notes (Douyin + Bilibili)

## Overview

This skill turns a Douyin or Bilibili (B站) URL into a local Markdown knowledge note. The user provides intent, approvals, and local cookies (mandatory for Douyin, optional for Bilibili); the agent sets up tools, downloads, transcribes on CPU, summarizes with the current AI, renames the note from content, and reports every process/output location.

## Platform Detection

Inspect the URL before any setup:

| Domain | Platform | Downloader | Cookie |
|---|---|---|---|
| `douyin.com` / `*.douyin.com` | 抖音 | DouK-Downloader | **Mandatory** |
| `bilibili.com` / `b23.tv` | B站 | yt-dlp | **Optional** (try without first) |

If the URL matches neither, stop and tell the user this skill currently only supports Douyin and Bilibili.

## Non-Negotiable Rules

- **Cookie-first (Douyin)**: Douyin requires cookies. Do not waste a no-cookie attempt. Ask for a local cookie file path before download.
- **Cookie-optional (Bilibili)**: try yt-dlp without cookies first. If the download fails with an auth/anti-bot error (HTTP 403, HTTP 412, "需要登录", "Precondition Failed"), ask for a Bilibili cookie file path.
- **Approval UX**: do not ask the user to type `y`, `yes`, `1`, or any confirmation text. Any consent must be requested through the agent's ask/approval mechanism.
- **Current-AI summary**: after ASR creates `transcript.txt`, the AI currently executing this skill reads it and writes the summary. Do not default to Ollama/local LLM.
- **CPU transcription**: faster-whisper must run with `--device cpu --compute-type int8` unless the user explicitly requests GPU and confirms CUDA works.
- **Content filename**: do not leave the final note named only as an id. Derive a short title from the AI analysis, sanitize it, rename the Markdown file, and report the final path.
- **Completion report**: always tell the user where process files, installed dependencies, caches, transcript, audio, video, cookies, and final notes are located.

## First Response

If the URL is Douyin, say:

> I can set up the open-source tools, download the Douyin video with your local cookies, extract audio, transcribe on CPU, summarize it myself, and save a renamed Markdown note. I will ask for approvals through the agent UI, not by making you type confirmations. At the end I will report where all process files and outputs were written.

If the URL is Bilibili, say:

> I can set up the open-source tools, download the Bilibili video (no cookies needed for public videos), extract audio, transcribe on CPU, summarize it myself, and save a renamed Markdown note. I will ask for approvals through the agent UI, not by making you type confirmations. At the end I will report where all process files and outputs were written.

If the user hasn't provided a URL yet, say a combined version and ask for the URL first.

Collect only:

1. Video URL (Douyin or Bilibili).
2. For Douyin: local cookie file path, such as `<workspace>\cookies.txt`. For Bilibili: only ask if the no-cookie attempt fails.
3. Workspace path, or suggest a neutral default such as `%USERPROFILE%\video2md`.
4. Knowledge output directory, or default to `<workspace>\knowledge`.
5. Agent approvals for network installs, browser access, closing browser, or GUI/manual initialization.

## Bootstrap Order

### Step 0: Detect Platform

Parse the URL. Determine Douyin vs Bilibili. All subsequent steps branch on this.

### Step 1: Common Setup (Both Platforms)

1. Locate or clone `https://github.com/leebrown316868/dy_vedio2md.git` into `<workspace>`.
2. Locate Git Bash, Python 3.10+, FFmpeg, and the project scripts. Use discovered absolute paths.
3. Choose `<tool-cache>`, preferably `%LOCALAPPDATA%\video2md-run` on Windows.
4. Prepare faster-whisper dependencies under `<tool-cache>\asr-deps`; model/cache files go under `<tool-cache>\hf-cache`.

### Step 2A: Douyin Download

1. Prepare DouK/TikTokDownloader in `<tool-cache>\DouK-Downloader`; dependency installs go under `<tool-cache>\douk-deps`.
2. Verify cookie file exists, is non-empty, and contains likely Douyin cookie names (`sessionid`/`sid_guard`, `odin_tt`, `ttwid`). Print names/count only, never values.
3. Run download via `scripts/run_douyin_once.py` with absolute `--run-dir`, `--output-dir`, `--douk-dir`, and `--cookie-file`.
4. Video lands at `<run-dir>\source.mp4`. If missing, search `DouK-Downloader/Volume/Download/**/*.mp4` as fallback (see Douyin Download Rules).

### Step 2B: Bilibili Download

1. Ensure `yt-dlp` is available. If not, install it:
   ```bash
   <python> -m pip install --target "<tool-cache>/ytdlp-deps" yt-dlp
   ```
   Or use system pip: `pip install yt-dlp`.
2. No GUI initialization needed — yt-dlp has no interactive first-run step.
3. **First attempt — no cookies with stable yt-dlp:**
   ```bash
   yt-dlp -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" -o "<run-dir>\source.mp4" "<url>"
   ```
4. **If stable yt-dlp fails with HTTP 412 (Precondition Failed) or wbi sign error:**
   B站 API changes frequently and stable yt-dlp may lag behind. Upgrade to nightly and retry:
   ```bash
   pip install --upgrade --pre yt-dlp
   ```
   Then retry the same download command from step 3. If nightly also fails, proceed to step 5.
5. **If download still fails (HTTP 403, HTTP 412, "需要登录", auth/anti-bot errors):**
   Ask the user for a Bilibili cookie file, then:
   - **Cookie format auto-conversion**: yt-dlp `--cookies` requires Netscape format (tab-separated fields with domain/path/expiry). The user's raw `Cookie:` header value (`key=value; key=value`) is NOT Netscape format. Always convert:
     ```python
     # Read raw cookie text, convert to Netscape format for .bilibili.com
     import time
     text = open(cookie_path, encoding='utf-8').read().strip()
     if text.lower().startswith('cookie:'):
         text = text.split(':', 1)[1].strip()
     expiry = int(time.time()) + 60*60*24*30
     lines = ['# Netscape HTTP Cookie File']
     for part in text.split(';'):
         part = part.strip()
         if not part or '=' not in part:
             continue
         name, value = part.split('=', 1)
         name = name.strip()
         if not name:
             continue
         for domain, subdomains in [('.bilibili.com', 'TRUE'), ('bilibili.com', 'FALSE')]:
             lines.append('\t'.join([domain, subdomains, '/', 'FALSE', str(expiry), name, value]))
     netscape_path = Path(cookie_path).with_suffix('.netscape.txt')
     open(netscape_path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
     ```
     Then download with the converted file:
     ```bash
     yt-dlp --cookies "<netscape_cookie_path>" -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" -o "<run-dir>\source.mp4" "<url>"
     ```
6. **Do NOT use `--cookies-from-browser` on Windows**: Edge/Chrome cookie databases are often locked (browser running) or fail DPAPI decryption. Always ask the user for a local cookie file instead.
7. B站 cookie file key names to verify: `SESSDATA`, `bili_jct`, `buvid3`. Print names/count only, never values.
8. yt-dlp outputs directly to the specified path — no fallback search needed.

### Step 3: Audio Extraction (Both Platforms)

```bash
ffmpeg -y -i "<run-dir>\source.mp4" -vn -ac 1 -ar 16000 "<run-dir>\audio.wav"
```

### Step 4: Transcription (Both Platforms)

```bash
--transcribe-pythonpath "<tool-cache>/asr-deps"
--transcribe-env "HF_HOME=<tool-cache>/hf-cache"
--transcribe-command '<python> scripts/transcribe_faster_whisper.py "{audio}" "{transcript}" --model base --device cpu --compute-type int8 --language auto'
```

### Step 5: Summarize & Rename (Both Platforms)

1. Read `transcript.txt`, summarize with the current AI, write/update Markdown.
2. Rename the Markdown file using a content-derived title (see Filename Rule).

### Step 6: Completion Report (Both Platforms)

Give the completion report using the appropriate template below.

## Why CUDA Errors Happen

`cublas64_12.dll` errors happen when faster-whisper/CTranslate2 tries CUDA but the machine lacks compatible CUDA runtime DLLs. Avoid this for zero-base users by always passing `--device cpu --compute-type int8`. Do not let `device=auto` decide.

## Completion Report

End every successful run with a compact report. Use the template matching the actual platform.

### Douyin Report

| Item | Path |
| --- | --- |
| Workspace/repo | `<workspace>` |
| Tool cache | `<tool-cache>` |
| Download tool | DouK-Downloader (`<tool-cache>\DouK-Downloader`) |
| DouK deps | `<tool-cache>\douk-deps` |
| ASR deps | `<tool-cache>\asr-deps` |
| ASR/model cache | `<tool-cache>\hf-cache` |
| Cookie file | `<cookie-file>` (values not shown) |
| Run dir | `<workspace>\runs\<id>` |
| Source video | `<run-dir>\source.mp4` |
| Audio | `<run-dir>\audio.wav` |
| Transcript | `<run-dir>\transcript.txt` |
| Final note | `<knowledge>\<content-title>.md` |

### Bilibili Report

| Item | Path |
| --- | --- |
| Workspace/repo | `<workspace>` |
| Tool cache | `<tool-cache>` |
| Download tool | yt-dlp (`<tool-cache>\ytdlp-deps` or system) |
| ASR deps | `<tool-cache>\asr-deps` |
| ASR/model cache | `<tool-cache>\hf-cache` |
| Cookie file | `<cookie-file>` or "none (public video)" |
| Run dir | `<workspace>\runs\<id>` |
| Source video | `<run-dir>\source.mp4` |
| Audio | `<run-dir>\audio.wav` |
| Transcript | `<run-dir>\transcript.txt` |
| Final note | `<knowledge>\<content-title>.md` |

Also state what was cleaned:
- Douyin: temporary DouK cookie settings restored.
- Bilibili: usually nothing (yt-dlp leaves no persistent state).

If files remain intentionally, say so; do not delete user artifacts unless explicitly asked.

## Filename Rule

After summarizing, infer a concise Chinese title from the actual content, not from the video id. Sanitize it for Windows filenames:

- Remove `<>:"/\|?*` and control characters.
- Keep it under about 60 characters.
- If the title collides, append `-2`, `-3`, etc.
- Rename the Markdown note to `<title>.md`.
- The final user-facing sentence must use the content title path, not `knowledge\<video-id>.md`.

## Approval Rules

- Use the agent's ask/approval mechanism for installs, browser access, process closing, and visible/manual GUI steps.
- Do not write prompts like "please type yes" or "enter 1 to confirm".
- If a CLI requires interactive confirmation, first obtain agent approval, then automate the CLI input yourself when safe. For account/security actions, stop and use agent ask.

## Douyin Download Rules (DouK)

- DouK must be initialized before automation. If `Volume/settings.json` is missing, ask through agent approval before visible/manual initialization.
- Use absolute paths for `run-dir`, `output-dir`, and DouK `root`.
- Restore/clear temporary DouK cookie settings after the run.
- If target run dir has no MP4, search `DouK-Downloader/Volume/Download/**/*.mp4`, copy the newest matching file to `<run-dir>\source.mp4`, and resume from FFmpeg.
- If menu piping fails, do not repeat the same sequence. Check initialization, paths, and default download dir, then ask for approval before any manual/visible fallback.

## Bilibili Download Rules (yt-dlp)

- No GUI, no interactive initialization, no `settings.json`.
- Default format: `bestvideo[height<=1080]+bestaudio/best[height<=1080]`. If the user requests 4K, adjust the height filter.
- yt-dlp outputs the video directly to the specified path — no need to search fallback directories.
- If yt-dlp is not installed, install it to `<tool-cache>\ytdlp-deps` (isolated) or use system pip.
- **yt-dlp nightly fallback**: B站 API changes frequently. If stable yt-dlp fails with HTTP 412 (Precondition Failed / wbi sign), upgrade to nightly with `pip install --upgrade --pre yt-dlp` and retry before asking for cookies. Nightly often has fixes that stable hasn't released yet.
- **Cookie format conversion is mandatory**: yt-dlp `--cookies` requires Netscape format (tab-separated: `domain flag path secure expiry name value`). The raw `Cookie:` header value from browser DevTools (`key=value; key=value`) will be rejected with `'does not look like a Netscape format cookies file'`. Always convert using the script in Step 2B.5. Write the converted file next to the original as `<cookie-file>.netscape.txt`.
- **Avoid `--cookies-from-browser` on Windows**: Edge locks its cookie DB while running; Chrome DPAPI decryption often fails. These are systemic Windows limitations, not transient errors. Don't waste attempts — go straight to asking for a local cookie file.
- If all attempts (stable + nightly + no-cookie, stable + nightly + cookie-file) fail: report the error and stop. Do not loop.
- B站 short links (`b23.tv`) are supported — yt-dlp resolves them automatically.

## Red Flags

- Trying Douyin download without cookies.
- Forcing Bilibili cookie requirement before the first download attempt.
- Asking the user to paste cookies into chat.
- Asking the user to type confirmation text instead of using agent ask.
- Printing cookie values or request headers.
- Running faster-whisper with `device=auto` or without `--device cpu --compute-type int8`.
- Leaving final note named as a raw video id.
- Saying only "saved to ..." without reporting process file locations.
- Assuming Git Bash has `python` or that paths match the developer's machine.
- Using DouK for a Bilibili URL or yt-dlp for a Douyin URL.
- Using `--cookies-from-browser` on Windows — it fails when browsers are running (Edge lock) or can't decrypt (Chrome DPAPI).
- Passing raw Cookie header format directly to `yt-dlp --cookies` without converting to Netscape format.
- Giving up after stable yt-dlp fails without trying nightly first.

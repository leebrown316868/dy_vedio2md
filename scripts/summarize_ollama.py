from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


PROMPT = """请把下面的视频转写稿整理成中文知识库笔记。

要求：
1. 用 Markdown 输出。
2. 先给 5 条以内核心要点。
3. 再给结构化摘要。
4. 最后列出适合放入知识库的标签。

转写稿：
{transcript}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a transcript with a local Ollama model.")
    parser.add_argument("transcript", type=Path)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    args = parser.parse_args()

    text = args.transcript.read_text(encoding="utf-8")
    payload = {
        "model": args.model,
        "prompt": PROMPT.format(transcript=text),
        "stream": False,
    }
    request = urllib.request.Request(
        f"{args.host.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read().decode("utf-8"))

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(body["response"].strip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

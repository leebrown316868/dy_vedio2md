# video2md

把视频里的中文口播内容整理成 Markdown 知识库笔记的本地 CLI。

当前版本是轻量编排器：它不绑定某一个抖音下载器、ASR 或 LLM，而是通过命令模板串起这些工具。

## 0 基础使用方式：让 Codex 按 Skill 带跑

如果你不熟悉 Git、Python、FFmpeg、DouK、ASR 或命令行，推荐先使用仓库内置的 Codex Skill：

```text
skills/capturing-douyin-video-notes
```

把这个目录复制到你的 Codex skills 目录，例如：

```powershell
Copy-Item -Recurse .\skills\capturing-douyin-video-notes "$env:USERPROFILE\.codex\skills\capturing-douyin-video-notes"
```

然后在 Codex 里说：

```text
$capturing-douyin-video-notes 帮我把这个抖音视频转成知识库笔记：https://www.douyin.com/video/...
```

这个 Skill 会引导 AI 自动完成：

- clone 或定位本项目
- 准备 Git Bash、Python、DouK-Downloader、FFmpeg、ASR 依赖
- 在需要登录态时，指导你把抖音 Cookie 保存到本地 `cookies.txt`
- 下载视频、抽音频、转写、总结、写入 Markdown
- 遇到 Windows 引号、相对路径、DouK 下载记录等问题时按内置恢复流程处理

人类只需要负责：提供视频 URL、同意安装/读取浏览器/关闭浏览器等敏感操作、在需要时本地保存 Cookie。不要把 Cookie 发到聊天里。

## 流程

```text
URL 或本地视频
-> 下载/复制视频
-> FFmpeg 提取音频
-> ASR 转写
-> LLM 总结
-> 写入 Markdown 知识库目录
```

## 安装依赖

最少需要 Python 3.10+。

根据你的实际流程安装这些外部工具：

- 下载：`yt-dlp`、TikTokDownloader、Douyin_TikTok_Download_API 或其他能保存视频文件的工具
- 抽音频：`ffmpeg`
- 转写：`faster-whisper`、FunASR 或其他能把音频写成文本文件的工具
- 总结：本地 `Ollama` 或任意能把转写稿写成 Markdown 文件的命令

本项目自带两个可选脚本：

- `scripts/transcribe_faster_whisper.py`
- `scripts/summarize_ollama.py`
- `scripts/cookies_to_netscape.py`
- `scripts/run_douyin_once.py`

## 快速开始

如果已经有转写稿，可以先跳过下载和转写，验证 Markdown 生成：

```bash
python -m video2md "手动导入" \
  --title "测试视频" \
  --transcript-file ./transcript.txt \
  --output-dir ./knowledge
```

生成结果会写到：

```text
knowledge/测试视频.md
```

## 处理 URL

示例使用 `yt-dlp` 下载、`ffmpeg` 抽音频、`faster-whisper` 转写、`Ollama` 总结：

```bash
python -m video2md "https://www.douyin.com/video/xxx" \
  --title "抖音视频笔记" \
  --download-command 'yt-dlp -o "{video}" "{url}"' \
  --transcribe-command 'python scripts/transcribe_faster_whisper.py "{audio}" "{transcript}" --model small' \
  --summarize-command 'python scripts/summarize_ollama.py "{transcript}" "{summary}" --model qwen2.5:7b' \
  --output-dir ./knowledge \
  --work-dir ./runs/douyin-001
```

注意：抖音网页内容经常需要浏览器 Cookie，下载命令是否可用取决于你选择的下载器。只要下载器能把视频保存到 `{video}`，就能接进这个流程。

## 抖音快速上手

推荐路线是 `DouK-Downloader + cookies.txt + video2md`。这条路线已经实测跑通，比直接用 `yt-dlp` 更适合中国抖音。

### 1. 准备 DouK-Downloader

```bash
mkdir -p C:/tmp/video2md-run
cd C:/tmp/video2md-run
git clone --depth 1 https://github.com/JoeanAmier/TikTokDownloader.git DouK-Downloader
cd DouK-Downloader
python -m pip install -r requirements.txt
python main.py
```

首次运行按提示选择语言并同意免责声明，让它生成 `Volume/settings.json`。

### 2. 准备 Cookie

不要把 Cookie 发到聊天或远程服务。只放到本机文件：

```text
E:\project\video2md\cookies.txt
```

获取方式：

1. 用浏览器打开并登录 `https://www.douyin.com/`。
2. 打开目标视频页。
3. 按 `F12` 打开开发者工具，切到 `网络/Network`。
4. 勾选“保留日志”，刷新页面。
5. 点任意一个 `www.douyin.com` 请求。
6. 右侧进入 `标头/Headers`，找到 `请求标头/Request Headers`。
7. 复制 `Cookie:` 后面的整串内容到 `cookies.txt`。

如果复制的是整段 `Cookie: xxx=...` 也可以；脚本会自动去掉前缀。`cookies.txt` 里应能看到类似这些 cookie 名称：`sessionid`、`sid_guard`、`uid_tt`、`odin_tt`、`ttwid`。

### 3. 一条命令跑完整流程

下面命令会自动检查 Cookie、调用 DouK 下载、复制视频、FFmpeg 抽音频、faster-whisper 转写、生成 Markdown。

```bash
python scripts/run_douyin_once.py "https://www.douyin.com/video/7585139447092546852" \
  --title "马云2017纽约彭博全球商业论坛演讲" \
  --cookie-file cookies.txt \
  --douk-dir C:/tmp/video2md-run/DouK-Downloader \
  --douk-pythonpath C:/tmp/video2md-run/douk-deps \
  --run-dir runs/7585139447092546852 \
  --output-dir knowledge \
  --ffmpeg "C:/Users/ASUS/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1-full_build/bin/ffmpeg.exe" \
  --transcribe-command 'set PYTHONPATH=C:\tmp\video2md-run\asr-deps&& set HF_HOME=C:\tmp\video2md-run\hf-cache&& python scripts\transcribe_faster_whisper.py "{audio}" "{transcript}" --model base --device cpu --compute-type int8 --language auto'
```

如果你已经有 Ollama，可以再加总结命令：

```bash
--summarize-command 'python scripts/summarize_ollama.py "{transcript}" "{summary}" --model qwen2.5:7b'
```

没有本地 LLM 时，也可以先只生成转写稿，再手动或用其他模型总结。

## 这次实测踩坑

### 人类必须做的部分

- 登录抖音网页。
- 从 DevTools 的 `Headers -> Request Headers -> Cookie` 复制 Cookie 到本地 `cookies.txt`。
- 对读取 Cookie、关闭浏览器这类敏感操作做明确授权。

这些步骤涉及账号凭据，默认不应该由 AI 偷偷读取或上传。

### 程序/AI 可以做的部分

- 检查 `cookies.txt` 是否为空、是否包含关键 Cookie 名称。
- 把 Cookie 写入 DouK 的临时配置，并在结束后清理。
- 下载视频。
- 定位 mp4。
- 用 FFmpeg 抽音频。
- 用 faster-whisper/FunASR 转写。
- 用 LLM 总结。
- 写入 `knowledge/*.md`。

### 最容易踩的坑

- 在 DevTools 的 `负载/Payload` 里找 Cookie。正确位置是 `标头/Headers`。
- 只复制了 `msToken`、`a_bogus` 等请求参数，而不是完整 `Cookie` 请求头。
- 期待 AI 自动读取 Edge Cookie。Windows DPAPI 可能禁止当前进程解密浏览器 Cookie。
- Edge 还在运行时，`yt-dlp --cookies-from-browser edge` 可能因为数据库被锁而失败。
- `yt-dlp` 即使拿到 Cookie，也可能因为抖音接口/签名变化失败；DouK-Downloader 当前更稳。
- 页面能播放不代表能直接下载，抖音网页里的视频常是 `blob:` 地址。
- 第一次转写需要安装 ASR 依赖并下载模型。

### 推荐边界

安全、现实的自动化边界是：

```text
人类手动提供本地 cookies.txt
-> 程序自动下载/转写/总结/入库
```

不推荐让程序默认读取浏览器 Cookie、绕过 DPAPI、自动处理验证码或上传登录态。

## 命令模板

支持的占位符：

- 下载命令：`{url}`、`{video}`
- 抽音频命令：`{video}`、`{audio}`
- 转写命令：`{audio}`、`{transcript}`
- 总结命令：`{transcript}`、`{summary}`

路径里可能有空格时，请在模板里给占位符加引号，例如 `"{audio}"`。

也可以用环境变量固定默认命令：

```bash
export VIDEO2MD_DOWNLOAD_COMMAND='yt-dlp -o "{video}" "{url}"'
export VIDEO2MD_TRANSCRIBE_COMMAND='python scripts/transcribe_faster_whisper.py "{audio}" "{transcript}" --model small'
export VIDEO2MD_SUMMARIZE_COMMAND='python scripts/summarize_ollama.py "{transcript}" "{summary}" --model qwen2.5:7b'
```

## 输出格式

每篇笔记包含：

- 标题
- 原始来源
- 创建时间
- LLM 摘要
- 完整转写稿

如果不传 `--summarize-command`，笔记会只包含转写稿。

## 测试

```bash
python -m unittest tests.test_pipeline -v
```

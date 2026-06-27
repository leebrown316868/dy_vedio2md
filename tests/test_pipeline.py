import tempfile
import unittest
from pathlib import Path

from video2md.pipeline import PipelineConfig, run_pipeline


class FakeRunner:
    def __init__(self):
        self.commands = []

    def __call__(self, command):
        self.commands.append(command)
        parts = command.split()
        if parts[0] == "transcribe":
            Path(parts[-1]).write_text("第一段内容。\n第二段内容。", encoding="utf-8")
        if parts[0] == "summarize":
            Path(parts[-1]).write_text("## 总结\n- 要点一\n- 要点二", encoding="utf-8")


class PipelineTest(unittest.TestCase):
    def test_pipeline_writes_markdown_note_from_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            runner = FakeRunner()

            result = run_pipeline(
                source="https://www.douyin.com/video/example",
                config=PipelineConfig(
                    output_dir=workspace / "notes",
                    work_dir=workspace / "work",
                    title="测试视频",
                    download_command="download {url} {video}",
                    extract_command="extract {video} {audio}",
                    transcribe_command="transcribe {audio} {transcript}",
                    summarize_command="summarize {transcript} {summary}",
                ),
                runner=runner,
            )

            self.assertEqual(
                runner.commands,
                [
                    "download https://www.douyin.com/video/example "
                    + str(workspace / "work" / "source.mp4"),
                    "extract "
                    + str(workspace / "work" / "source.mp4")
                    + " "
                    + str(workspace / "work" / "audio.wav"),
                    "transcribe "
                    + str(workspace / "work" / "audio.wav")
                    + " "
                    + str(workspace / "work" / "transcript.txt"),
                    "summarize "
                    + str(workspace / "work" / "transcript.txt")
                    + " "
                    + str(workspace / "work" / "summary.md"),
                ],
            )
            note = result.note_path.read_text(encoding="utf-8")
            self.assertIn("# 测试视频", note)
            self.assertIn("https://www.douyin.com/video/example", note)
            self.assertIn("## 总结", note)
            self.assertIn("第一段内容。", note)

    def test_pipeline_accepts_existing_transcript_without_media_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            transcript = workspace / "manual.txt"
            transcript.write_text("已经整理好的文字。", encoding="utf-8")
            runner = FakeRunner()

            result = run_pipeline(
                source=str(transcript),
                config=PipelineConfig(
                    output_dir=workspace / "notes",
                    work_dir=workspace / "work",
                    title="手动稿",
                    transcript_file=transcript,
                ),
                runner=runner,
            )

            self.assertEqual(runner.commands, [])
            note = result.note_path.read_text(encoding="utf-8")
            self.assertIn("# 手动稿", note)
            self.assertIn("已经整理好的文字。", note)


if __name__ == "__main__":
    unittest.main()

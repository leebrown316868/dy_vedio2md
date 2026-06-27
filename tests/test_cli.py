import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTest(unittest.TestCase):
    def test_cli_writes_note_from_existing_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            transcript = workspace / "transcript.txt"
            transcript.write_text("CLI transcript line.", encoding="utf-8")
            output_dir = workspace / "knowledge"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "video2md",
                    "manual-import",
                    "--title",
                    "sample-video",
                    "--transcript-file",
                    str(transcript),
                    "--output-dir",
                    str(output_dir),
                    "--work-dir",
                    str(workspace / "work"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            note_path = Path(completed.stdout.strip())
            self.assertEqual(note_path.name, "sample-video.md")
            self.assertTrue(note_path.exists())
            self.assertIn("CLI transcript line.", note_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

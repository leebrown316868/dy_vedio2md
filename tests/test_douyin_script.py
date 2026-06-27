import tempfile
import unittest
import os
import contextlib
import io
from pathlib import Path

from scripts.run_douyin_once import (
    _check_cookie,
    _command_env,
    _find_downloaded_video,
    _newest_video,
    _read_cookie,
    _resolve_path,
)


class DouyinScriptTest(unittest.TestCase):
    def test_check_cookie_rejects_missing_douyin_keys(self):
        with self.assertRaises(SystemExit) as error:
            _check_cookie("foo=bar")

        self.assertIn("sessionid", str(error.exception))
        self.assertIn("odin_tt", str(error.exception))
        self.assertIn("ttwid", str(error.exception))

    def test_newest_video_prefers_file_not_seen_before(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "old.mp4"
            new = root / "nested" / "new.mp4"
            old.write_text("old", encoding="utf-8")
            new.parent.mkdir()
            new.write_text("new", encoding="utf-8")

            self.assertEqual(_newest_video(root, {old}), new)

    def test_read_cookie_allows_no_cookie_path_for_first_attempt(self):
        self.assertEqual(_read_cookie(None), "")

    def test_command_env_adds_pythonpath_and_key_value_pairs_without_shell_syntax(self):
        env = _command_env(
            {"PYTHONPATH": "base", "KEEP": "1"},
            pythonpath="extra",
            pairs=["HF_HOME=C:/cache/hf", "EMPTY="],
        )

        self.assertEqual(env["PYTHONPATH"], f"extra{os.pathsep}base")
        self.assertEqual(env["HF_HOME"], "C:/cache/hf")
        self.assertEqual(env["EMPTY"], "")
        self.assertEqual(env["KEEP"], "1")

    def test_command_env_rejects_env_pair_without_equals(self):
        with self.assertRaises(SystemExit) as error:
            _command_env({}, pythonpath="", pairs=["HF_HOME"])

        self.assertIn("KEY=VALUE", str(error.exception))

    def test_find_downloaded_video_falls_back_to_douk_default_download_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "run" / "douk-output"
            fallback = root / "DouK-Downloader" / "Volume" / "Download"
            output.mkdir(parents=True)
            fallback.mkdir(parents=True)
            video = fallback / "cached.mp4"
            video.write_text("video", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(_find_downloaded_video(output, set(), [fallback]), video)

    def test_resolve_path_returns_absolute_path(self):
        self.assertTrue(_resolve_path(Path("runs/example")).is_absolute())


if __name__ == "__main__":
    unittest.main()

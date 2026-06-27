import tempfile
import unittest
from pathlib import Path

from scripts.run_douyin_once import _check_cookie, _newest_video


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


if __name__ == "__main__":
    unittest.main()

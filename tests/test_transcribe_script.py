import unittest

from scripts.transcribe_faster_whisper import build_parser


class TranscribeScriptTest(unittest.TestCase):
    def test_defaults_to_cpu_int8_to_avoid_cuda_dependency(self):
        args = build_parser().parse_args(["audio.wav", "transcript.txt"])

        self.assertEqual(args.device, "cpu")
        self.assertEqual(args.compute_type, "int8")


if __name__ == "__main__":
    unittest.main()

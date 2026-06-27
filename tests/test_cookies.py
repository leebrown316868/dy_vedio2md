import unittest

from video2md.cookies import inspect_cookie_header, to_netscape_cookie_text


class CookieTest(unittest.TestCase):
    def test_inspect_cookie_header_reports_names_without_values(self):
        report = inspect_cookie_header(
            "Cookie: sessionid=secret-session; odin_tt=secret-odin; ttwid=secret-ttwid"
        )

        self.assertEqual(report.count, 3)
        self.assertTrue(report.has_session_cookie)
        self.assertTrue(report.has_odin_tt)
        self.assertTrue(report.has_ttwid)
        self.assertEqual(report.names, ["sessionid", "odin_tt", "ttwid"])
        self.assertNotIn("secret", repr(report))

    def test_to_netscape_cookie_text_converts_each_cookie_for_douyin_domains(self):
        text = to_netscape_cookie_text(
            "Cookie: sessionid=abc; odin_tt=def",
            expiry=2000000000,
        )

        self.assertIn("# Netscape HTTP Cookie File", text)
        self.assertIn(".douyin.com\tTRUE\t/\tFALSE\t2000000000\tsessionid\tabc", text)
        self.assertIn("douyin.com\tFALSE\t/\tFALSE\t2000000000\todin_tt\tdef", text)


if __name__ == "__main__":
    unittest.main()

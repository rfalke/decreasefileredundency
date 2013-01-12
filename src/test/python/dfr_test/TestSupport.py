
import unittest
import argparse

from dfr.support import abspath, chunker, format_bytes, format_time_delta, add_common_command_line_arguments
from dfr_test.utils import TestCase


class Test(TestCase):

    def test_abspath(self):
        self.assertTrue(abspath(".").startswith("/"))

    def test_chunker(self):
        self.assertEqual(list(chunker([], 2)), [])
        self.assertEqual(list(chunker([1], 2)), [[1]])
        self.assertEqual(list(chunker([1, 2], 2)), [[1, 2]])
        self.assertEqual(list(chunker([1, 2, 3], 2)), [[1, 2], [3]])
        self.assertEqual(list(chunker([1, 2, 3, 4], 2)), [[1, 2], [3, 4]])

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0")
        self.assertEqual(format_bytes(1), "1")
        self.assertEqual(format_bytes(2), "2")
        self.assertEqual(format_bytes(999), "999")
        self.assertEqual(format_bytes(1000), "1,000")
        self.assertEqual(format_bytes(1023), "1,023")
        self.assertEqual(format_bytes(1024), "1,024 (1.0 KiB)")
        self.assertEqual(format_bytes(2048), "2,048 (2.0 KiB)")
        self.assertEqual(format_bytes(414747471), "414,747,471 (395.5 MiB)")
        self.assertEqual(format_bytes(34418050942), "34,418,050,942 (32.1 GiB)")
        self.assertEqual(format_bytes(2000*(2**40)), "2,199,023,255,552,000 (2000.0 TiB)")
        self.assertEqual(format_bytes(2*(10**15)), "2,000,000,000,000,000 (1819.0 TiB)")

    def test_format_time_delta(self):
        self.assertEqual(format_time_delta(0), "0s")
        self.assertEqual(format_time_delta(59), "59s")
        self.assertEqual(format_time_delta(60), "1m 0s")
        self.assertEqual(format_time_delta(71), "1m 11s")
        self.assertEqual(format_time_delta(3600), "1h 0m")
        self.assertEqual(format_time_delta(24*3600), "1d 0h")

    def test_add_common_command_line_arguments(self):
        parser = argparse.ArgumentParser()
        add_common_command_line_arguments(parser)

        default_db = parser.parse_args([]).db[0]
        self.assertTrue(default_db.startswith("/"))
        self.assertTrue(default_db.endswith("files.sdb"))
        self.assertEqual(parser.parse_args(["--db-file", "foo"]).db[0], "foo")
        self.assertEqual(parser.parse_args(["--db-file=foo"]).db[0], "foo")

if __name__ == '__main__':
    unittest.main()

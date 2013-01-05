
import os
import unittest
from tempdir import TempDir

from dfr.bit_hashing import get_sha1sums
from dfr_test.utils import write_binary


class Test(unittest.TestCase):

    def test_empty_file(self):
        with TempDir() as tmpdir:
            tmpfn = os.path.join(tmpdir.name, 'input')
            write_binary(0, tmpfn)
            self.assertRaises(AssertionError, get_sha1sums, tmpfn, os.path.getsize(tmpfn), 1024)

    def test_1023_file(self):
        with TempDir() as tmpdir:
            tmpfn = os.path.join(tmpdir.name, 'input')
            write_binary(1023, tmpfn)
            self.assertRaises(AssertionError, get_sha1sums, tmpfn, os.path.getsize(tmpfn), 1024)

    def test_1024_file(self):
        with TempDir() as tmpdir:
            tmpfn = os.path.join(tmpdir.name, 'input')
            write_binary(1024, tmpfn)
            hashs = get_sha1sums(tmpfn, os.path.getsize(tmpfn), 1024)
            self.assertEqual(hashs, ('5b00669c480d5cffbdfa8bdba99561160f2d1b77', '5b00669c480d5cffbdfa8bdba99561160f2d1b77', {}))

    def test_1025_bytes_file(self):
        with TempDir() as tmpdir:
            tmpfn = os.path.join(tmpdir.name, 'input')
            write_binary(1025, tmpfn)
            hashs = get_sha1sums(tmpfn, os.path.getsize(tmpfn), 1024)
            self.assertEqual(hashs, ('5b00669c480d5cffbdfa8bdba99561160f2d1b77', '409c9978384c2832af4a98bafe453dfdaa8e8054', {}))

    def test_2049_bytes_file(self):
        with TempDir() as tmpdir:
            tmpfn = os.path.join(tmpdir.name, 'input')
            write_binary(2049, tmpfn)
            hashs = get_sha1sums(tmpfn, os.path.getsize(tmpfn), 1024)
            self.assertEqual(hashs, ('5b00669c480d5cffbdfa8bdba99561160f2d1b77', '170751534f1a95fd80a7a25787ecad2b60368e0a',
                                     {2048L: 'f10ccfde60c17db26e7d85d35665c7661dbbeb2c'}))

if __name__ == '__main__':
    unittest.main()

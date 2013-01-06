
import os
import unittest
from tempdir import TempDir

from dfr.bit_hashing import get_sha1sums, get_partial_sha1
from dfr_test.utils import write_binary, write_big_binary


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
            self.assertEqual(get_partial_sha1(tmpfn, 0, 1024), '5b00669c480d5cffbdfa8bdba99561160f2d1b77')
            self.assertEqual(get_partial_sha1(tmpfn, 0, 2048), 'f10ccfde60c17db26e7d85d35665c7661dbbeb2c')
            self.assertEqual(get_partial_sha1(tmpfn, 0, 2049), '170751534f1a95fd80a7a25787ecad2b60368e0a')

    def test_larger_file(self):
        with TempDir() as tmpdir:
            tmpfn = os.path.join(tmpdir.name, 'input')
            write_big_binary(5, tmpfn)
            hashs = get_sha1sums(tmpfn, os.path.getsize(tmpfn), 1024)
            self.assertEqual(hashs, ('5b00669c480d5cffbdfa8bdba99561160f2d1b77', '598bb31d8995839ba2d700f0bd911b5546d0d836',
                                     {2048L: 'f10ccfde60c17db26e7d85d35665c7661dbbeb2c',
                                      4096L: 'e9dded8c84614e894501965af60c2525794a8c7d',
                                      8192L: 'ecca46e1a1d0a6012713b09a870d84f695b6d9b0',
                                      16384L: '80cb9c430d80c3084649f65e0ca25dabbffb1b62',
                                      32768L: '1edf14b9f91477ed8071b1f66e2d4c2849501b91',
                                      65536L: 'f04977267a391b2c8f7ad8e070f149bc19b0fc25',
                                      131072L: 'f826028ed472b1fadeddbf54fc1912a095d28795',
                                      262144L: '37ef77696fc255bf53b4cdd014b223676f2dc8bb',
                                      524288L: '6c10df9ee9fa4b1c8495b19becb7f8ae8a07ad96',
                                      1048576L: 'ecfc8e86fdd83811f9cc9bf500993b63069923be',
                                      2097152L: '3394ba403303c0784f836bdb1ee13a4bfd14e6de',
                                      4194304L: 'd697024ed93ff625330d050391ade99cd5cbddad'
                                      }))

    def test_file_of_buffer_size(self):
        with TempDir() as tmpdir:
            tmpfn = os.path.join(tmpdir.name, 'input')
            write_big_binary(4, tmpfn)
            hashs = get_sha1sums(tmpfn, os.path.getsize(tmpfn), 1024)
            self.assertEqual(hashs, ('5b00669c480d5cffbdfa8bdba99561160f2d1b77', 'd697024ed93ff625330d050391ade99cd5cbddad',
                                     {2048L: 'f10ccfde60c17db26e7d85d35665c7661dbbeb2c',
                                      4096L: 'e9dded8c84614e894501965af60c2525794a8c7d',
                                      8192L: 'ecca46e1a1d0a6012713b09a870d84f695b6d9b0',
                                      16384L: '80cb9c430d80c3084649f65e0ca25dabbffb1b62',
                                      32768L: '1edf14b9f91477ed8071b1f66e2d4c2849501b91',
                                      65536L: 'f04977267a391b2c8f7ad8e070f149bc19b0fc25',
                                      131072L: 'f826028ed472b1fadeddbf54fc1912a095d28795',
                                      262144L: '37ef77696fc255bf53b4cdd014b223676f2dc8bb',
                                      524288L: '6c10df9ee9fa4b1c8495b19becb7f8ae8a07ad96',
                                      1048576L: 'ecfc8e86fdd83811f9cc9bf500993b63069923be',
                                      2097152L: '3394ba403303c0784f836bdb1ee13a4bfd14e6de'
                                      }))

if __name__ == '__main__':
    unittest.main()


import os
import stat
import unittest
import contextlib
import sys


def write_binary(size, filename, offset=0):
    out = open(filename, "wb")
    for i in range(size):
        out.write(chr((i+offset) % 256))
    out.close()
    assert os.path.getsize(filename) == size


def write_big_binary(megabytes, filename, offset=0):
    one_mb = 2**20
    buffer = "".join([chr((x+offset) % 256) for x in range(256)])
    while len(buffer) != one_mb:
        buffer += buffer

    out = open(filename, "wb")
    for _ in range(megabytes):
        out.write(buffer)
    out.close()
    assert os.path.getsize(filename) == one_mb*megabytes


def make_unwriteable(path):
    mode = os.stat(path).st_mode
    assert (mode & stat.S_IWUSR) == stat.S_IWUSR
    new_mode = mode - stat.S_IWUSR
    os.chmod(path, new_mode)


class TestCase(unittest.TestCase):

    def assert_lists_have_same_items(self, actual_list, expected_list):
        self.assertEqual(len(actual_list), len(expected_list))
        for i in actual_list:
            self.assertTrue(i in expected_list)
        for i in expected_list:
            self.assertTrue(i in actual_list)


@contextlib.contextmanager
def nostderr():
    class Devnull(object):
        def write(self, _):
            pass

        def flush(self):
            pass

    savestderr = sys.stderr
    sys.stderr = Devnull()
    yield
    sys.stderr = savestderr

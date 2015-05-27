
import os
import stat
import unittest
import sys

DO_NOT_MATCH_RE = "^$"


def write_binary(size, filename, offset=0, add=None):
    out = open(filename, "wb")
    for i in range(size):
        out.write(chr((i+offset) % 256))
    if add is None:
        add = []
    for i in add:
        out.write(chr(i % 256))
    out.close()
    assert os.path.getsize(filename) == size+len(add)


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


def make_unreadable(path):
    mode = os.stat(path).st_mode
    assert (mode & stat.S_IRUSR) == stat.S_IRUSR
    new_mode = mode - stat.S_IRUSR
    os.chmod(path, new_mode)


class TestCase(unittest.TestCase):

    def assert_lists_have_same_items(self, actual_list, expected_list):
        for i in actual_list:
            self.assertTrue(i in expected_list, "The actual item %r is not expected" % (i,))
        for i in expected_list:
            self.assertTrue(i in actual_list, "The expected item %r was not found" % (i,))
        self.assertEqual(len(actual_list), len(expected_list))

    def assert_no_exception(self):
        pass


class Devnull(object):
    def __init__(self, written):
        self.written = written

    def write(self, msg):
        self.written[0] += msg

    def flush(self):
        pass


class NoStderr(object):
    def __init__(self):
        self._written = None
        self.savestderr = None

    def __enter__(self):
        self.savestderr = sys.stderr
        self._written = [""]
        sys.stderr = Devnull(self._written)
        return self

    def __exit__(self, type, value, traceback):
        sys.stderr = self.savestderr

    def written(self):
        return self._written[0]

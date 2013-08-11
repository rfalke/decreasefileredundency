
import unittest
import time

from dfr.progress import Progress
from dfr_test.utils import TestCase, NoStderr


class Test(TestCase):

    def test_simple(self):
        with NoStderr():
            prog = Progress(10, "calculating")
            prog.work(0)
            for _ in range(10):
                prog.work()
                time.sleep(0.1)

            prog.finish()
        self.assertTrue(True)

    def test_format(self):
        todo = 1000000000000
        with NoStderr():
            prog = Progress(todo, "calculating")
            time.sleep(1)
            prog.work(todo)
            prog.finish()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()

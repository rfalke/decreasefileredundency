
from tempdir import TempDir
import os
from os.path import join
import unittest

from dfr import db
from dfr_test.utils import TestCase
from dfr.bit_indexer import BitIndexer
from dfr.bit_truncated_finder import BitTruncatedFinder


def write_chunked(filename, *chunks):
    out = open(filename, "wb")
    for size, char in chunks:
        for _ in range(size):
            out.write(chr(char % 256))
    out.close()
    assert os.path.getsize(filename) == sum([x[0] for x in chunks])


class Test(TestCase):

    def test_simple(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir('data')
            write_chunked(join(datadir, 'input_1'), (9000, 0))
            write_chunked(join(datadir, 'input_2'), (9000, 0), (1, 1))
            write_chunked(join(datadir, 'input_3'), (9000, 0), (1, 2))
            write_chunked(join(datadir, 'input_4'), (9000, 0), (1, 1), (1, 2))
            write_chunked(join(datadir, 'input_5'), (9000, 0), (1, 2))
            write_chunked(join(datadir, 'input_6'), (9000, 0), (1, 2))
            write_chunked(join(datadir, 'input_7'), (5000, 0), (3999, 1))
            write_chunked(join(datadir, 'input_8'), (8999, 0))
            write_chunked(join(datadir, 'input_9'), (4000, 10))
            write_chunked(join(datadir, 'input_10'), (4001, 10))

            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)

            indexer = BitIndexer(the_db, verbose_progress=0)
            indexer.run([datadir])

            os.remove(join(datadir, 'input_2'))
            os.remove(join(datadir, 'input_10'))

            finder = BitTruncatedFinder(db.Database(db_fn, verbose=0), [datadir])
            items = list(finder.find())
            items = [(x.large_size, x.large_path, x.small_size, x.small_path) for x in items]
            self.assertEqual(items, [
                (9002, join(datadir, 'input_4'), 9000, join(datadir, 'input_1')),
                (9002, join(datadir, 'input_4'), 8999, join(datadir, 'input_8')),
                (9001, join(datadir, 'input_3'), 9000, join(datadir, 'input_1')),
                (9001, join(datadir, 'input_5'), 9000, join(datadir, 'input_1')),
                (9001, join(datadir, 'input_6'), 9000, join(datadir, 'input_1')),
                (9001, join(datadir, 'input_3'), 8999, join(datadir, 'input_8')),
                (9001, join(datadir, 'input_5'), 8999, join(datadir, 'input_8')),
                (9001, join(datadir, 'input_6'), 8999, join(datadir, 'input_8')),
                (9000, join(datadir, 'input_1'), 8999, join(datadir, 'input_8'))])

if __name__ == '__main__':
    unittest.main()

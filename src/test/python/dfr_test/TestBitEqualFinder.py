
from tempdir import TempDir
import os
import unittest
from os.path import join

from dfr import db
from dfr_test.utils import write_binary, TestCase
from dfr.bit_indexer import BitIndexer
from dfr.bit_equal_finder import BitEqualFinder


class Test(TestCase):

    def test_simple(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir('data')
            write_binary(1024, join(datadir, 'hash1_a'))
            write_binary(1024, join(datadir, 'hash1_b'))
            write_binary(1024, join(datadir, 'hash1_c'))
            write_binary(1100, join(datadir, 'hash2_a'), offset=1)
            write_binary(1100, join(datadir, 'hash2_b'), offset=1)
            write_binary(1100, join(datadir, 'hash2_c'), offset=1)
            write_binary(1024, join(datadir, 'hash3'), offset=2)
            write_binary(1024, join(datadir, 'hash4_a'), offset=3)
            os.link(join(datadir, 'hash4_a'), join(datadir, 'hash4_b'))

            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)

            indexer = BitIndexer(the_db, verbose_progress=0)
            indexer.run([datadir])

            os.remove(join(datadir, 'hash2_c'))

            finder = BitEqualFinder(db.Database(db_fn, verbose=0), [datadir])
            items = list(finder.find())
            items = [(x.size, x.hardlinked, x.path1, x.path2) for x in items]

            self.assertEqual(items, [
                (1100, False, join(datadir, 'hash2_a'), join(datadir, 'hash2_b')),

                (1024, False, join(datadir, 'hash1_a'), join(datadir, 'hash1_b')),
                (1024, False, join(datadir, 'hash1_a'), join(datadir, 'hash1_c')),
                (1024, False, join(datadir, 'hash1_b'), join(datadir, 'hash1_c')),

                (1024, True, join(datadir, 'hash4_a'), join(datadir, 'hash4_b'))])

    def test_with_subdirs(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir("data")
            subdir1 = tmpdir.create_dir("data", "sub1")
            subdir2 = tmpdir.create_dir("data", "sub2")

            write_binary(1024, join(subdir2, 'hash1_a'))
            write_binary(1024, join(subdir1, 'hash1_b'))
            write_binary(1024, join(subdir1, 'hash1_c'))
            write_binary(1024, join(datadir, 'hash1_d'))

            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)

            indexer = BitIndexer(the_db, verbose_progress=0)
            indexer.run([datadir])

            finder = BitEqualFinder(db.Database(db_fn, verbose=0), [datadir])
            items = list(finder.find())
            items = [(x.size, x.hardlinked, x.path1, x.path2) for x in items]
            self.assertEqual(items, [
                (1024, False, join(datadir, 'hash1_d'), join(subdir1, 'hash1_b')),
                (1024, False, join(datadir, 'hash1_d'), join(subdir1, 'hash1_c')),
                (1024, False, join(datadir, 'hash1_d'), join(subdir2, 'hash1_a')),
                (1024, False, join(subdir1, 'hash1_b'), join(subdir1, 'hash1_c')),
                (1024, False, join(subdir1, 'hash1_b'), join(subdir2, 'hash1_a')),
                (1024, False, join(subdir1, 'hash1_c'), join(subdir2, 'hash1_a'))])

            finder = BitEqualFinder(db.Database(db_fn, verbose=0), [subdir1])
            items = list(finder.find())
            items = [(x.size, x.hardlinked, x.path1, x.path2) for x in items]
            self.assertEqual(items, [
                (1024, False, join(subdir1, 'hash1_b'), join(subdir1, 'hash1_c'))])

if __name__ == '__main__':
    unittest.main()

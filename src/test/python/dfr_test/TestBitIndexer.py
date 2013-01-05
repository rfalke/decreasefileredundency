
from tempdir import TempDir
import os
import unittest
import sqlite3
import time

from dfr.bit_indexer import BitIndexer
from dfr import db

from dfr_test.utils import write_binary


class Test(unittest.TestCase):

    def test_simple(self):
        with TempDir() as tmpdir:
            datadir = os.path.join(tmpdir.name, 'data')
            subdir1 = os.path.join(datadir, 'sub1')
            subdir2 = os.path.join(datadir, 'sub2')
            os.makedirs(subdir1)
            os.makedirs(subdir2)
            write_binary(1024, os.path.join(subdir1, 'input1'))
            write_binary(1025, os.path.join(subdir1, 'input2'))
            write_binary(1026, os.path.join(subdir2, 'input3'))

            db_fn = os.path.join(tmpdir.name, 'files.db')
            indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=0)
            indexer.run([datadir])

            conn = sqlite3.connect(db_fn)
            self.assertEqual(conn.execute("select * from dir").fetchall(),
                             [(1, datadir), (2, subdir1), (3, subdir2)])
            self.assertEqual(conn.execute("select id,dirid,name,contentid from file").fetchall(),
                             [(1, 2, u'input1', 1), (2, 2, u'input2', 2), (3, 3, u'input3', 3)])
            self.assertEqual(conn.execute("select * from content").fetchall(),
                             [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', 1024, u''),
                              (2, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'409c9978384c2832af4a98bafe453dfdaa8e8054', 1025, u''),
                              (3, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'76f936767b092576521501bdb344aa7a632b88b8', 1026, u'')])

            indexer.run([datadir])

            self.assertEqual(conn.execute("select * from dir").fetchall(),
                             [(1, datadir), (2, subdir1), (3, subdir2)])
            self.assertEqual(conn.execute("select id,dirid,name,contentid from file").fetchall(),
                             [(1, 2, u'input1', 1), (2, 2, u'input2', 2), (3, 3, u'input3', 3)])
            self.assertEqual(conn.execute("select * from content").fetchall(),
                             [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', 1024, u''),
                              (2, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'409c9978384c2832af4a98bafe453dfdaa8e8054', 1025, u''),
                              (3, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'76f936767b092576521501bdb344aa7a632b88b8', 1026, u'')])

    def test_content_changes(self):
        with TempDir() as tmpdir:
            datadir = os.path.join(tmpdir.name, 'data')
            os.makedirs(datadir)
            write_binary(1024, os.path.join(datadir, 'input'))

            db_fn = os.path.join(tmpdir.name, 'files.db')
            indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=0)
            indexer.run([datadir])

            conn = sqlite3.connect(db_fn)
            self.assertEqual(conn.execute("select contentid,fullsha1 from file,content where file.contentid=content.id").fetchall(),
                             [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77')])

            time.sleep(2)
            write_binary(1024, os.path.join(datadir, 'input'), offset=1)
            indexer.run([datadir])

            self.assertEqual(conn.execute("select contentid,fullsha1 from file,content where file.contentid=content.id").fetchall(),
                             [(2, u'b0f14f1c1d87185bcc46363860b84609d5a2169e')])


if __name__ == '__main__':
    unittest.main()

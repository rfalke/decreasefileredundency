
from tempdir import TempDir
import os
import unittest
import sqlite3
import time
import errno
from os.path import join

from dfr.bit_indexer import BitIndexer
from dfr import db
from dfr_test.utils import write_binary, TestCase, NoStderr, make_unreadable


class Test(TestCase):

    def test_simple(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir("data")
            subdir1 = tmpdir.create_dir("data", "sub1")
            subdir2 = tmpdir.create_dir("data", "sub2")

            write_binary(100, join(subdir1, 'small_file'))
            write_binary(1024, join(subdir1, 'input1'))
            write_binary(1025, join(subdir1, 'input2'))
            write_binary(1026, join(subdir2, 'input3'))

            os.symlink("input1", join(subdir1, 'symlink'))
            os.mkfifo(join(subdir1, 'fifo'))

            db_fn = join(tmpdir.name, 'files.sdb')
            indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=0)
            indexer.run([datadir])

            conn = sqlite3.connect(db_fn)
            self.assertEqual(conn.execute("select * from dir").fetchall(),
                             [(1, datadir), (2, subdir1), (3, subdir2)])
            self.assertEqual(conn.execute("select id,dirid,name,contentid from file").fetchall(),
                             [(1, 2, u'input1', 1), (2, 2, u'input2', 2), (3, 3, u'input3', 3)])
            self.assertEqual(conn.execute("select * from content").fetchall(),
                             [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', 1024, u'', -1),
                              (2, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'409c9978384c2832af4a98bafe453dfdaa8e8054', 1025, u'', -1),
                              (3, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'76f936767b092576521501bdb344aa7a632b88b8', 1026, u'', -1)])

            indexer.run([datadir])

            self.assertEqual(conn.execute("select * from dir").fetchall(),
                             [(1, datadir), (2, subdir1), (3, subdir2)])
            self.assertEqual(conn.execute("select id,dirid,name,contentid from file").fetchall(),
                             [(1, 2, u'input1', 1), (2, 2, u'input2', 2), (3, 3, u'input3', 3)])
            self.assertEqual(conn.execute("select * from content").fetchall(),
                             [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', 1024, u'', -1),
                              (2, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'409c9978384c2832af4a98bafe453dfdaa8e8054', 1025, u'', -1),
                              (3, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'76f936767b092576521501bdb344aa7a632b88b8', 1026, u'', -1)])

    def test_removed_file(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir("data")
            subdir1 = tmpdir.create_dir("data", "sub1")
            subdir2 = tmpdir.create_dir("data", "sub2")

            write_binary(1024, join(subdir1, 'input1'))
            write_binary(1025, join(subdir1, 'input2'))
            write_binary(1026, join(subdir2, 'input3'))

            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            indexer = BitIndexer(the_db, verbose_progress=0)
            indexer.run([datadir])

            conn = sqlite3.connect(db_fn)
            self.assertEqual(conn.execute("select * from dir").fetchall(),
                             [(1, datadir), (2, subdir1), (3, subdir2)])
            self.assertEqual(conn.execute("select id,dirid,name,contentid from file").fetchall(),
                             [(1, 2, u'input1', 1), (2, 2, u'input2', 2), (3, 3, u'input3', 3)])
            self.assertEqual(conn.execute("select * from content").fetchall(),
                             [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', 1024, u'', -1),
                              (2, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'409c9978384c2832af4a98bafe453dfdaa8e8054', 1025, u'', -1),
                              (3, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'76f936767b092576521501bdb344aa7a632b88b8', 1026, u'', -1)])

            os.remove(join(subdir1, 'input1'))
            indexer.run([datadir])

            self.assertEqual(conn.execute("select * from dir").fetchall(),
                             [(1, datadir), (2, subdir1), (3, subdir2)])
            self.assertEqual(conn.execute("select id,dirid,name,contentid from file").fetchall(),
                             [(2, 2, u'input2', 2), (3, 3, u'input3', 3)])
            self.assertEqual(conn.execute("select * from content").fetchall(),
                             [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', 1024, u'', -1),
                              (2, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'409c9978384c2832af4a98bafe453dfdaa8e8054', 1025, u'', -1),
                              (3, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'76f936767b092576521501bdb344aa7a632b88b8', 1026, u'', -1)])

    def test_content_changes(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir('data')
            write_binary(1024, join(datadir, 'input'))

            db_fn = join(tmpdir.name, 'files.sdb')
            indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=0)
            indexer.run([datadir])

            conn = sqlite3.connect(db_fn)
            self.assertEqual(conn.execute("select contentid,fullsha1 from file,content where file.contentid=content.id").fetchall(),
                             [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77')])
            new_mtime = time.time() + 2
            write_binary(1024, join(datadir, 'input'), offset=1)
            os.utime(join(datadir, 'input'), (new_mtime, new_mtime))
            indexer.run([datadir])

            self.assertEqual(conn.execute("select contentid,fullsha1 from file,content where file.contentid=content.id").fetchall(),
                             [(2, u'b0f14f1c1d87185bcc46363860b84609d5a2169e')])

    def test_progress_for_coverage(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir('data')
            write_binary(1024, join(datadir, 'input'))

            db_fn = join(tmpdir.name, 'files.sdb')
            with NoStderr():
                indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=1)
                indexer.run([datadir])
            self.assertTrue(True)

    def test_unreadable_file(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir('data')
            write_binary(1024, join(datadir, 'input'))
            make_unreadable(join(datadir, 'input'))

            db_fn = join(tmpdir.name, 'files.sdb')
            indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=1)
            with NoStderr() as devnull:
                indexer.run([datadir])
                self.assertEqual(devnull.written(), "[P]\n")

    def test_other_io_error(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir('data')
            write_binary(1024, join(datadir, 'input'))

            db_fn = join(tmpdir.name, 'files.sdb')
            indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=1)

            def mock(*_):
                error = IOError("dummy io error")
                error.errno = errno.EBADFD
                raise error

            indexer.get_or_insert_content = mock
            with NoStderr() as devnull:
                indexer.run([datadir])
                self.assertEqual(devnull.written(), "[E]\n")

    def test_file_names(self):
        with TempDir() as tmpdir:
            datadir = join(tmpdir.name, 'data')
            names = []
            names.append("all_chars_part1_%s" % ("".join([unichr(x) for x in range(1, 80)])))
            names.append("all_chars_part2_%s" % ("".join([unichr(x) for x in range(80, 160)])))
            names.append("all_chars_part3_%s" % ("".join([unichr(x) for x in range(160, 240)])))
            names.append("all_chars_part4_%s" % ("".join([unichr(x) for x in range(240, 256)])))

            for name in names:
                name = name.replace("/", "")
                subdir = tmpdir.create_dir('data', name)
                write_binary(1024, join(subdir, name))

            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            indexer = BitIndexer(the_db, verbose_progress=1)
            with NoStderr() as devnull:
                indexer.run([datadir])
            self.assertTrue(len(the_db.file.find_ids()), len(names))

            with NoStderr() as devnull:
                indexer.run([datadir])
                self.assertEqual(devnull.written(), "[]"*(1+len(names))+"\n")
            self.assertTrue(len(the_db.file.find_ids()), len(names))

    def test_image_detection(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir("data")
            out = open(join(datadir, 'input'), "w")
            out.write("\x89PNG\r\n\x1a\n" + (" " * 1024))
            out.close()

            db_fn = join(tmpdir.name, 'files.sdb')
            indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=0)
            indexer.run([datadir])

            conn = sqlite3.connect(db_fn)
            self.assertEqual(conn.execute("select * from content").fetchall(),
                             [(1, u'a128af6716f4a73cc0a490ee5ba2fd87a56823fe', u'04c942989681cbf2933bef10eb4afcc5312c9b3f', 1032, u'', None)])

    def test_commit_every_mostly_for_coverage(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir("data")

            for i in range(1000):
                write_binary(1024, join(datadir, 'input_%03d' % i))

            db_fn = join(tmpdir.name, 'files.sdb')
            indexer = BitIndexer(db.Database(db_fn, verbose=0), verbose_progress=0, commit_every=0.01)
            indexer.run([datadir])
            self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()

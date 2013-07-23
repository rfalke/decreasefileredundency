
from tempdir import TempDir
import unittest
import sqlite3
from os.path import join

from dfr.bit_indexer import BitIndexer
from dfr.image_indexer import ImageIndexer
from dfr import db
from dfr_test.utils import TestCase, DO_NOT_MATCH_RE, NoStderr


class Test(TestCase):

    def test_simple(self):
        with TempDir(0) as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            indexer = BitIndexer(the_db, DO_NOT_MATCH_RE, DO_NOT_MATCH_RE, verbose_progress=0)
            indexer.run(["src/test/images/big"])

            indexer = ImageIndexer(the_db, verbose_progress=0)
            indexer.run()

            self.verify_db_rows_for_big_images(db_fn)

    def test_multithreading(self):
        with TempDir(0) as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            indexer = BitIndexer(the_db, DO_NOT_MATCH_RE, DO_NOT_MATCH_RE, verbose_progress=0)
            indexer.run(["src/test/images/big"])

            indexer = ImageIndexer(the_db, verbose_progress=0, commit_every=0.01, parallel_threads=4)
            indexer.run()

            self.verify_db_rows_for_big_images(db_fn)

    def test_nothing_to_index(self):
        with TempDir(0) as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)

            indexer = ImageIndexer(the_db, verbose_progress=0)
            indexer.run()

            self.assertTrue(len(the_db.content.find()) == 0)

    def verify_db_rows_for_big_images(self, db_fn):
        conn = sqlite3.connect(db_fn)
        rows = conn.execute("SELECT file.name, imagehash.iht, imagehash.hash " +
                            "FROM file,content,imagehash " +
                            "WHERE file.contentid = content.id AND content.id = imagehash.contentid " +
                            "ORDER BY file.name").fetchall()
        self.assertEqual(len(rows), 4 * 11)
        self.assertIn((u'Nice-Bee.jpeg', 1, u'646 d3c f3f da9 e83 13da 1c6b 1d4c 1faa 17ce 18d7 f31 92b 50f 29a 326 60a d23 b5e a61 afa c71 1285 1a25 256c 1a4f 1f47 1a3d e0d 67f 253 2d9 ca3 13e3 ce4 92b 7fc 90d 745 79e 90d b88 ea1 188c 203b 26ac 1a31 c9f'), rows)
        self.assertIn((u'Nice-Bee.jpeg', 2, u'c000c000c3fec3ffc7ffc7ff8fff1fff7fff7fff7ffe0ff801f8e1fcf9ffffc7'), rows)
        self.assertIn((u'Nice-Bee.jpeg', 3, u'cd3ac3371dab6360'), rows)
        self.assertIn((u'Nice-Bee.jpeg', 4, u'eff8f0c080d7f93c'), rows)

    def test_coverage(self):
        with TempDir() as tmpdir:
            datadir = tmpdir.create_dir("data")
            base = open("src/test/images/big/Nice-Bee.jpeg").read()
            for i in range(50):
                name = join(datadir, 'input_%d' % i)
                out = open(name, "w")
                out.write(base)
                out.write(str(i))
                out.close()

            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            indexer = BitIndexer(the_db, DO_NOT_MATCH_RE, DO_NOT_MATCH_RE, verbose_progress=0)
            indexer.run([datadir])

            with NoStderr():
                indexer = ImageIndexer(the_db, verbose_progress=5, commit_every=0.01)
                indexer.run()

            self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()

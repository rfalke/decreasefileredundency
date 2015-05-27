
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

            indexer = ImageIndexer(the_db, [1, 3, 4], verbose_progress=0)
            indexer.run()

            self.verify_db_rows_for_big_images(db_fn)

    def test_multithreading(self):
        with TempDir(0) as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            indexer = BitIndexer(the_db, DO_NOT_MATCH_RE, DO_NOT_MATCH_RE, verbose_progress=0)
            indexer.run(["src/test/images/big"])

            indexer = ImageIndexer(the_db, [1, 3, 4],
                                   verbose_progress=0, commit_every=0.01, parallel_threads=4)
            indexer.run()

            self.verify_db_rows_for_big_images(db_fn)

    def test_nothing_to_index(self):
        with TempDir(0) as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)

            indexer = ImageIndexer(the_db, [1], verbose_progress=0)
            indexer.run()

            self.assertTrue(len(the_db.content.find()) == 0)

    def verify_db_rows_for_big_images(self, db_fn):
        conn = sqlite3.connect(db_fn)
        rows = conn.execute("SELECT file.name, imagehash.iht, imagehash.hash " +
                            "FROM file,content,imagehash " +
                            "WHERE file.contentid = content.id AND content.id = imagehash.contentid " +
                            "ORDER BY file.name").fetchall()
        self.assertEqual(len(rows), 3 * 13)
        self.assertIn((u'Nice-Bee.jpeg', 1, u'651 d38 f3f da4 e83 13d6 1c71 1d49 1f96 17da 18d2 f36 92c 510 29d 328 607 d24 b5e a66 af5 c6e 128a 1a1f 256e 1a50 1f42 1a45 e09 680 254 2d8 ca4 13e7 cf3 92a 7ee 90a 74f 799 902 b81 e9a 1885 203e 26ba 1a2f ca5'), rows)
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
                indexer = ImageIndexer(the_db, [1], verbose_progress=5, commit_every=0.01)
                indexer.run()

            self.assert_no_exception()

if __name__ == '__main__':
    unittest.main()

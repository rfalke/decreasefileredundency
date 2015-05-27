
from tempdir import TempDir
import unittest
from os.path import join

from dfr.image_comperator import ImageComperator
from dfr import db
from dfr.model import Content, ImageHash
from dfr_test.utils import TestCase, NoStderr


def add_content_and_hash(the_db, content_id, sig, iht=3):
    the_db.content.save(Content(4096+content_id, 'fullsha1', 'first1ksha1', 'partsha1s', 1),
                        id_value=content_id)
    the_db.imagehash.save(ImageHash(content_id, iht, sig))
    the_db.commit()


class Test(TestCase):

    def test_nothing_to_index(self):
        with TempDir(0) as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.8)

            self.assertTrue(len(the_db.content.find()) == 0)

    def test_simple(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad2520000000')
            add_content_and_hash(the_db, 3, 'cac7ad252000000f')
            add_content_and_hash(the_db, 4, 'cac7ad252fffffff')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 3)

            for i in found:
                self.assertEqual(i.iht, 3)
                self.assertEqual(i.similarity_threshold, 0.9)
            self.assertEqual(found[0].pairs, '2:0 3:4')
            self.assertEqual(found[0].contentid, 1)
            self.assertEqual(found[0].score, 140)
            self.assertEqual(found[0].numpairs, 2)

            self.assertEqual(found[1].pairs, '1:0 3:4')
            self.assertEqual(found[1].contentid, 2)
            self.assertEqual(found[1].score, 140)
            self.assertEqual(found[1].numpairs, 2)

            self.assertEqual(found[2].pairs, '1:4 2:4')
            self.assertEqual(found[2].contentid, 3)
            self.assertEqual(found[2].score, 120)
            self.assertEqual(found[2].numpairs, 2)

            self.assertEqual(found[0].get_pairs(), [(2, 1.0), (3, 0.9375)])

    def test_executed_twice(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad2520000000')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 2)

            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 2)

    def test_rerun_with_loosend_similarity(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad2520000000')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 2)

            comperator.ensure_that_differences_are_calculated(0.8)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 2)
            found = found[0]
            self.assertEqual(found.similarity_threshold, 0.8)

    def test_executed_twice_with_new_content(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad2520000000')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 2)

            add_content_and_hash(the_db, 3, 'cac7ad2520000000')

            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 3)

    def test_iht1_gray(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, '0 0 0 da9 e83 13da 1c6b 1d4c 1faa 17ce 18d7 f31 92b 50f 29a 326', iht=1)
            add_content_and_hash(the_db, 2, 'fff 0 0 da9 e83 13da 1c6b 1d4c 1faa 17ce 18d7 f31 92b 50f 29a 326', iht=1)

            comperator = ImageComperator(the_db, 1, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.8)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 2)
            self.assertEqual(found[0].pairs, "2:0")
            self.assertEqual(found[1].pairs, "1:0")

    def test_iht1__rgb(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, '0 0 0 da9 e83 13da 1c6b 1d4c 1faa 17ce 18d7 f31 92b 50f 29a 326 60a d23 b5e a61 afa c71 1285 1a25 256c 1a4f 1f47 1a3d e0d 67f 253 2d9 ca3 13e3 ce4 92b 7fc 90d 745 79e 90d b88 ea1 188c 203b 26ac 1a31 c9f', iht=1)
            add_content_and_hash(the_db, 2, 'fff 0 0 da9 e83 13da 1c6b 1d4c 1faa 17ce 18d7 f31 92b 50f 29a 326 60a d23 b5e a61 afa c71 1285 1a25 256c 1a4f 1f47 1a3d e0d 67f 253 2d9 ca3 13e3 ce4 92b 7fc 90d 745 79e 90d b88 ea1 188c 203b 26ac 1a31 c9f', iht=1)

            comperator = ImageComperator(the_db, 1, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.8)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 2)
            self.assertEqual(found[0].pairs, "2:0")
            self.assertEqual(found[1].pairs, "1:0")

            self.assertEqual(found[0].get_pairs(), [(2, 1.0)])

    def test_iht2(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000', iht=2)
            add_content_and_hash(the_db, 2, 'cac7ad252000000f', iht=2)
            comperator = ImageComperator(the_db, 2, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.8)

            found = the_db.imagecmp.find()

            self.assertEqual(found[0].pairs, "2:4")
            self.assertEqual(found[1].pairs, "1:4")

    def test_ih3(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad252000000f')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 2)
            self.assertEqual(found[0].pairs, "2:4")
            self.assertEqual(found[1].pairs, "1:4")

    def test_ih4(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000', iht=4)
            add_content_and_hash(the_db, 2, 'cac7ad252000000f', iht=4)

            comperator = ImageComperator(the_db, 4, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 2)
            self.assertEqual(found[0].pairs, "2:4")
            self.assertEqual(found[1].pairs, "1:4")

    def test_ih5(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000', iht=5)
            add_content_and_hash(the_db, 2, 'cac7ad252000000f', iht=5)

            comperator = ImageComperator(the_db, 5, verbose_progress=0)
            comperator.ensure_that_differences_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 2)
            self.assertEqual(found[0].pairs, "2:4")
            self.assertEqual(found[1].pairs, "1:4")

    def test_coverage(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)

            with NoStderr():
                comperator = ImageComperator(the_db, 3, verbose_progress=5)
                comperator.ensure_that_differences_are_calculated(0.9)
                comperator.ensure_that_differences_are_calculated(0.9)
            self.assert_no_exception()


if __name__ == '__main__':
    unittest.main()

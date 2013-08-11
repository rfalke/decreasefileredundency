
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


def format_limits(image_cmp):
    return "[%d-%d]x[%d-%d]" % (
        image_cmp.contentid1_first, image_cmp.contentid1_last,
        image_cmp.contentid2_first, image_cmp.contentid2_last)


class Test(TestCase):

    def test_nothing_to_index(self):
        with TempDir(0) as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.8)

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
            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 1)
            found = found[0]
            self.assertEqual(format_limits(found), "[0-4]x[0-4]")
            self.assertEqual(found.iht, 3)
            self.assertEqual(found.similarity_threshold, 0.9)
            self.assert_lists_have_same_items(found.get_decoded_pairs(),
                                              [(1, 2, 1.0),
                                               (1, 3, 60/64.0),
                                               (2, 3, 60/64.0)])

    def test_two_tiles(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 567, 'cac7ad2520000000')
            add_content_and_hash(the_db, 1234, 'cac7ad252000000f')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual([format_limits(x) for x in found],
                             ['[0-999]x[0-999]',
                              '[0-999]x[1000-1234]',
                              '[1000-1234]x[1000-1234]'])
            self.assert_lists_have_same_items(found[0].get_decoded_pairs(), [])
            self.assert_lists_have_same_items(found[1].get_decoded_pairs(),
                                              [(567, 1234, 60/64.0)])
            self.assert_lists_have_same_items(found[2].get_decoded_pairs(), [])

    def test_executed_twice(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad2520000000')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 1)

            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 1)

    def test_rerun_with_loosend_similarity(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad2520000000')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 1)

            comperator.ensure_that_all_tiles_are_calculated(0.8)

            found = the_db.imagecmp.find()
            self.assertEqual(len(found), 1)
            found = found[0]
            self.assertEqual(found.similarity_threshold, 0.8)

    def test_executed_twice_with_new_content(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad2520000000')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual([format_limits(x) for x in found],
                             ['[0-2]x[0-2]'])

            add_content_and_hash(the_db, 3, 'cac7ad2520000000')

            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()
            self.assertEqual([format_limits(x) for x in found],
                             ['[0-3]x[0-3]'])

    def test_iht1(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, '0 0 0 da9 e83 13da 1c6b 1d4c 1faa 17ce 18d7 f31 92b 50f 29a 326 60a d23 b5e a61 afa c71 1285 1a25 256c 1a4f 1f47 1a3d e0d 67f 253 2d9 ca3 13e3 ce4 92b 7fc 90d 745 79e 90d b88 ea1 188c 203b 26ac 1a31 c9f', iht=1)
            add_content_and_hash(the_db, 2, 'fff 0 0 da9 e83 13da 1c6b 1d4c 1faa 17ce 18d7 f31 92b 50f 29a 326 60a d23 b5e a61 afa c71 1285 1a25 256c 1a4f 1f47 1a3d e0d 67f 253 2d9 ca3 13e3 ce4 92b 7fc 90d 745 79e 90d b88 ea1 188c 203b 26ac 1a31 c9f', iht=1)
            add_content_and_hash(the_db, 3, 'a25 256c 1a4f 1f47 1a3d e0d 67f 253 2d9 ca3 13e3 ce4 92b 7fc 90d 745 79e 90d b88 ea1 188c 203b 26ac 1a31 c9f', iht=1)

            comperator = ImageComperator(the_db, 1, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.8)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 1)
            found = found[0]
            self.assert_lists_have_same_items(found.get_decoded_pairs(),
                                              [(1, 2, 0.96876)])

    def test_iht2(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, '0000c000c3fec3ffc7ffc7ff8fff1fff7fff7fff7ffe0ff801f8e1fcf9ffffc7', iht=2)
            add_content_and_hash(the_db, 2, 'ff00c000c3fec3ffc7ffc7ff8fff1fff7fff7fff7ffe0ff801f8e1fcf9ffffc7', iht=2)
            comperator = ImageComperator(the_db, 2, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.8)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 1)
            found = found[0]
            self.assert_lists_have_same_items(found.get_decoded_pairs(),
                                              [(1, 2, (256-8)/256.0)])

    def test_ih3(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad252000000f')

            comperator = ImageComperator(the_db, 3, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 1)
            found = found[0]
            self.assert_lists_have_same_items(found.get_decoded_pairs(),
                                              [(1, 2, 60/64.0)])

    def test_ih4(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000', iht=4)
            add_content_and_hash(the_db, 2, 'cac7ad252000000f', iht=4)

            comperator = ImageComperator(the_db, 4, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 1)
            found = found[0]
            self.assert_lists_have_same_items(found.get_decoded_pairs(),
                                              [(1, 2, 60/64.0)])

    def test_ih5(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000', iht=5)
            add_content_and_hash(the_db, 2, 'cac7ad252000000f', iht=5)

            comperator = ImageComperator(the_db, 5, verbose_progress=0)
            comperator.ensure_that_all_tiles_are_calculated(0.9)

            found = the_db.imagecmp.find()

            self.assertEqual(len(found), 1)
            found = found[0]
            self.assert_lists_have_same_items(found.get_decoded_pairs(),
                                              [(1, 2, 60/64.0)])

    def test_coverage(self):
        with TempDir() as tmpdir:
            db_fn = join(tmpdir.name, 'files.sdb')
            the_db = db.Database(db_fn, verbose=0)
            add_content_and_hash(the_db, 1, 'cac7ad2520000000')
            add_content_and_hash(the_db, 2, 'cac7ad252000000f')

            with NoStderr():
                comperator = ImageComperator(the_db, 3, verbose_progress=5)
                comperator.ensure_that_all_tiles_are_calculated(0.9)
                comperator.ensure_that_all_tiles_are_calculated(0.9)
            self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()

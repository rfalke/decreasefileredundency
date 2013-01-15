
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

            self.verify_db_rows_for_big_images(db_fn)

    def verify_db_rows_for_big_images(self, db_fn):
        conn = sqlite3.connect(db_fn)
        rows = conn.execute("SELECT file.name, imagehash.iht, imagehash.hash " +
                            "FROM file,content,imagehash " +
                            "WHERE file.contentid = content.id AND content.id = imagehash.contentid " +
                            "ORDER BY file.name").fetchall()
        self.assert_lists_have_same_items(rows, [
            (u'Intercom_PCB_mit_Best.Druck.gif', 1, u'10000 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0'),
            (u'Intercom_PCB_mit_Best.Druck.gif', 2, u'ffffc07fc00fc00fc00fe01fe07fffffffffc07fc00fc00fc00fe01fe07fffff'),
            (u'NENG1614.bmp', 1, u'35ea 0 0 0 0 0 0 0 0 0 0 0 0 0 0 ca15'),
            (u'NENG1614.bmp', 2, u'7001f87ff8fffbfcfbc0ff807e00fe1ffc0ff8077007300720ef00ff000f0000'),
            (u'Nice-Bee.jpeg', 1, u'646 d3c f3f da9 e83 13da 1c6b 1d4c 1faa 17ce 18d7 f31 92b 50f 29a 326 60a d23 b5e a61 afa c71 1285 1a25 256c 1a4f 1f47 1a3d e0d 67f 253 2d9 ca3 13e3 ce4 92b 7fc 90d 745 79e 90d b88 ea1 188c 203b 26ac 1a31 c9f'),
            (u'Nice-Bee.jpeg', 2, u'80008000807880fec3fe87fe0fff1fff3ffe3ffe1ff803f801f88038f004f887'),
            (u'Organigramm_deut_2_Seewiesen-1_png.png', 1, u'352d 0 38c 0 2b4 58e 26f 1ed 34 29 31 909 dc 97 1ad ade9 19 0 8 3a caf 186 0 1b3 de9 b7f 45 1902 cd9 97 1ad ade9 19 0 0 0 2b4 0 38c 66c 175c 10a4 6b 1273 829 97 1ad ade9'),
            (u'Organigramm_deut_2_Seewiesen-1_png.png', 2, u'1fc03fe07fe0fff07ffe7ffe1ffe1ffe1ffe1ffe07f807f007c0078003800000'),
            (u'Sunflower_Metalhead64_edited.png', 1, u'100 444 62b 562 3ff 2c8 223 306 595 7d6 8da 9ba 98d 8c3 a1c a6cc c0a 937 a34 b4c b28 bc2 a71 7da 77c 85c b66 b6b c7c b25 436 6982 67d7 1735 d70 77c 156 5a 2c 1e 18 18 18 14 17 19 1c 695e'),
            (u'Sunflower_Metalhead64_edited.png', 2, u'000007c01ff03ff83ff87ffc7ffc7ffe7ffe7ffc3ff83ff81ff80ff003800000'),
            (u'bird_bird_bird_png_format_by_chimonk-d37tayt.png', 1, u'1a79 e01 f13 cd6 939 7e2 6fe 9ae 53f 647 8bc 531 356 296 1f0 7880 11b7 e54 cdb b75 ce2 b9d afe 8ea 726 71f 7d3 408 365 525 20d 767f 11b1 12b0 f12 a52 a03 70d 675 807 a1f 69a 669 4e6 3d8 375 33f 7c13'), (u'bird_bird_bird_png_format_by_chimonk-d37tayt.png', 2, u'01e003f0cff6efe6c7c4c7e047fc07fe2ffe2e3e087c0dfe09fe00fe00fe0030'),
            (u'free-your-mind-Seite2.bmp', 1, u'b93 0 0 0 0 0 0 0 0 0 0 0 0 0 0 f46c'),
            (u'free-your-mind-Seite2.bmp', 2, u'00001cc01fec06ec3ffe7ffe7ffe3ffc30f03ff81ff8070830e07ffc302c0000'),
            (u'globe_west_2048.jpeg', 1, u'69ac 150b 12e6 12f0 e0c cb2 c03 b1d ac3 940 717 5df 4f4 272 e7 48 64c7 1498 ef7 122b 117a e7a d8a bc2 b2a 9cd 7b2 600 556 2e8 109 47 60a8 275 78f fda 11e2 e4b cf0 eac 1077 f0f c6e a6d 8fa 615 32d 10c'),
            (u'globe_west_2048.jpeg', 2, u'fffffffff03fe01fc01fc00f800f800f801f8007c007c007e00ff00ffc3fffff'),
            (u'globe_west_2048.tiff', 1, None),
            (u'globe_west_2048.tiff', 2, u'fffffffff03fe01fc01fc00f800f800f801f8007c007c007e00ff00ffc3fffff'),
            (u'nice-map-big.jpeg', 1, u'197 119 17f 1a9 20b 207 22b 273 344 3e41 a0d 2de 369 42a 697 94d5 174 1b5 249 206 249 298 280 271 274 2d9 3e0 50e 9c8d 1014 b7b 2857 1de 214 3cb 415 460 a0d 40e 9aa 5628 60a 54e 7e3 3e4 458 405e 2605'),
            (u'nice-map-big.jpeg', 2, u'c70f870fc607c007781f310c078c9f9effbfffbe3f9e021fc03fe01fe01fe00f'),
            (u'sample_03.jpeg', 1, u'be9 103f f45 e94 ea2 ea6 ebf ef0 e62 d75 d6f f80 13fa 1865 1314 12c6 e43 177f 18cd 17ca 1662 149a 13ec 11ab f4a d62 ca0 da4 d23 a25 581 551 2d04 2689 2014 1aa8 17b2 1488 128d ea7 9d5 5e4 439 30a 2c5 38e 1c6 52d'),
            (u'sample_03.jpeg', 2, u'fffcfffcfffcbffc3ffc3fe411e460e0c0e000e001f003f007f90ffd0ff91ff8')])

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

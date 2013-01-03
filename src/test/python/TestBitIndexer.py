
from bit_indexer import BitIndexer
from tempdir import TempDir
import db
import random
import os,unittest,sqlite3

class Test(unittest.TestCase):

    def test_shuffle(self):
        with TempDir() as d:
            datadir=os.path.join(d.name, 'data')
            subdir1=os.path.join(datadir, 'sub1')
            subdir2=os.path.join(datadir, 'sub2')
            os.makedirs(subdir1)
            os.makedirs(subdir2)
            self.write_binary(1024, os.path.join(subdir1, 'input1'))
            self.write_binary(1025, os.path.join(subdir1, 'input2'))
            self.write_binary(1026, os.path.join(subdir2, 'input3'))

            db_fn=os.path.join(d.name, 'files.db')
            indexer=BitIndexer(db.Database(db_fn,verbose=0),verbose_progress=0)
            indexer.run([datadir])

            conn = sqlite3.connect(db_fn)
            self.assertEqual(conn.execute("select * from dir").fetchall(),
                             [(1, datadir), (2, subdir1), (3, subdir2)])
            self.assertEqual(conn.execute("select * from file").fetchall(),
                             [(1, 2, u'input1', 1), (2, 2, u'input2', 2), (3, 3, u'input3', 3)])
            self.assertEqual(conn.execute("select * from content").fetchall(),
                              [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', 1024, u''),
                               (2, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'409c9978384c2832af4a98bafe453dfdaa8e8054', 1025, u''),
                               (3, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'76f936767b092576521501bdb344aa7a632b88b8', 1026, u'')] )

            indexer.run([datadir])

            self.assertEqual(conn.execute("select * from dir").fetchall(),
                             [(1, datadir), (2, subdir1), (3, subdir2)])
            self.assertEqual(conn.execute("select * from file").fetchall(),
                             [(1, 2, u'input1', 1), (2, 2, u'input2', 2), (3, 3, u'input3', 3)])
            self.assertEqual(conn.execute("select * from content").fetchall(),
                              [(1, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', 1024, u''),
                               (2, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'409c9978384c2832af4a98bafe453dfdaa8e8054', 1025, u''),
                               (3, u'5b00669c480d5cffbdfa8bdba99561160f2d1b77', u'76f936767b092576521501bdb344aa7a632b88b8', 1026, u'')] )


    def write_binary(self,size,filename):
        f=open(filename,"wb")
        for i in range(size):
            f.write(chr(i % 256))
        f.close()
        assert os.path.getsize(filename)==size


if __name__ == '__main__':
    unittest.main()

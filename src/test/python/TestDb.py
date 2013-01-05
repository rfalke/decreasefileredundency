
from bit_indexer import BitIndexer
from tempdir import TempDir
import db
import random
import os,unittest,sqlite3,time
from model import *

class Test(unittest.TestCase):

    def assertContainsExactly(self, actualList, expectedList):
        self.assertEqual(len(actualList), len(expectedList))
        for i in actualList: self.assertTrue(i in expectedList)
        for i in expectedList: self.assertTrue(i in actualList)
        
    def test_dir_repo(self):
        with TempDir() as d:            
            db_fn=os.path.join(d.name, 'files.db')
            repo=db.Database(db_fn,verbose=0).dir

            obj1=Dir("foo")
            self.assertEqual(obj1, Dir("foo"))
            repo.save(obj1)
            self.assertEqual(obj1.id,1)
            self.assertEqual(obj1, Dir("foo", id=1))
            self.assertEqual(repo.load(1), obj1)

            obj2=Dir("bar")
            repo.save(obj2)
            self.assertEqual(obj2.id,2)

            self.assertContainsExactly(repo.find_ids(), [1,2])
            self.assertContainsExactly(repo.find_ids(name="foo"), [1])
            self.assertContainsExactly(repo.find_ids(id=2), [2])
            self.assertContainsExactly(repo.find_ids(name="hello"), [])

            self.assertContainsExactly(repo.find(), [obj1, obj2])
            self.assertContainsExactly(repo.find(name="foo"), [obj1])
            self.assertContainsExactly(repo.find(name="hello"), [])

            obj1.name="new"
            repo.save(obj1)
            
            self.assertEqual(repo.load(1), obj1)

            repo.delete(obj1)
            self.assertContainsExactly(repo.find_ids(), [2])            

    def test_file_repo(self):
        with TempDir() as d:            
            db_fn=os.path.join(d.name, 'files.db')
            repo=db.Database(db_fn,verbose=0).file

            obj1=File(1,"foo",2,3)
            self.assertEqual(obj1, File(1,"foo",2,3))
            repo.save(obj1)
            self.assertEqual(obj1.id,1)
            self.assertEqual(obj1, File(1,"foo",2,3, id=1))
            self.assertEqual(repo.load(1), obj1)

            obj2=File(1,"bar",4,5)
            repo.save(obj2)
            self.assertEqual(obj2.id,2)

            obj3=File(6,"foo",7,5)
            repo.save(obj3)
            self.assertEqual(obj3.id,3)

            self.assertContainsExactly(repo.find_ids(), [1,2,3])
            self.assertContainsExactly(repo.find_ids(name="foo"), [1,3])
            self.assertContainsExactly(repo.find_ids(id=2), [2])
            self.assertContainsExactly(repo.find_ids(dirid=1), [1,2])
            self.assertContainsExactly(repo.find_ids(contentid=5), [2,3])
            self.assertContainsExactly(repo.find_ids(name="hello"), [])

            self.assertContainsExactly(repo.find(), [obj1,obj2,obj3])
            self.assertContainsExactly(repo.find(name="foo"), [obj1,obj3])
            self.assertContainsExactly(repo.find(id=2), [obj2])
            self.assertContainsExactly(repo.find(dirid=1), [obj1,obj2])
            self.assertContainsExactly(repo.find(contentid=5), [obj2,obj3])
            self.assertContainsExactly(repo.find(name="hello"), [])

            obj1.name="new"
            obj1.dirid=20
            obj1.contentid=21
            repo.save(obj1)

            self.assertEqual(repo.load(1), obj1)

            repo.delete(obj1)
            self.assertContainsExactly(repo.find_ids(), [2,3])            

    def test_content_repo(self):
        with TempDir() as d:            
            db_fn=os.path.join(d.name, 'files.db')
            repo=db.Database(db_fn,verbose=0).content

            obj1=Content(1, "a", "b", "c")
            self.assertEqual(obj1, Content(1,"a", "b", "c"))
            repo.save(obj1)
            self.assertEqual(obj1.id,1)
            self.assertEqual(obj1, Content(1,"a", "b", "c", id=1))
            self.assertEqual(repo.load(1), obj1)

            obj2=Content(2,"a", "d", "e")
            repo.save(obj2)
            self.assertEqual(obj2.id,2)

            obj3=Content(1,"f", "g", "e")
            repo.save(obj3)
            self.assertEqual(obj3.id,3)

            self.assertContainsExactly(repo.find_ids(), [1,2,3])
            self.assertContainsExactly(repo.find_ids(size=1), [1,3])
            self.assertContainsExactly(repo.find_ids(id=2), [2])
            self.assertContainsExactly(repo.find_ids(fullsha1="a"), [1,2])
            self.assertContainsExactly(repo.find_ids(partsha1s="e"), [2,3])
            self.assertContainsExactly(repo.find_ids(size=99), [])

            self.assertContainsExactly(repo.find(), [obj1,obj2,obj3])
            self.assertContainsExactly(repo.find(size=1), [obj1,obj3])
            self.assertContainsExactly(repo.find(id=2), [obj2])
            self.assertContainsExactly(repo.find(fullsha1="a"), [obj1,obj2])
            self.assertContainsExactly(repo.find(partsha1s="e"), [obj2,obj3])
            self.assertContainsExactly(repo.find(size=99), [])

            obj1.size=20
            obj1.fullsha1="x"
            obj1.first1ksha1="y"
            obj1.partsha1sfullsha1="z"
            repo.save(obj1)
            
            self.assertEqual(repo.load(1), obj1)

            repo.delete(obj1)
            self.assertContainsExactly(repo.find_ids(), [2,3])

if __name__ == '__main__':
    unittest.main()

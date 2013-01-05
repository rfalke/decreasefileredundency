
from tempdir import TempDir
import os
import unittest
from sqlite3 import IntegrityError

from dfr import db
from dfr.model import Dir, File, Content
from dfr_test.utils import make_unwriteable, TestCase, nostderr


class Test(TestCase):

    def test_get_default_db_file(self):
        self.assertTrue(db.get_default_db_file().startswith(os.path.expanduser("~")))
        self.assertTrue(db.get_default_db_file().startswith("/home/"))

    def test_missing_db_dir(self):
        with TempDir() as tmpdir:
            make_unwriteable(tmpdir.name)
            db_name = os.path.join(tmpdir.name, "subdir", "files.db")
            self.assertRaises(OSError, db.Database, db_name)

    def test_sql_error(self):
        with TempDir() as tmpdir:
            db_name = os.path.join(tmpdir.name, "files.db")
            repo = db.Database(db_name, verbose=0).dir
            repo.save(Dir("foo"))
            with nostderr():
                self.assertRaises(IntegrityError, repo.save, Dir("foo"))

    def test_abstract_construct_method(self):
        with TempDir() as tmpdir:
            db_name = os.path.join(tmpdir.name, "files.db")
            the_db = db.Database(db_name, verbose=0)
            repo = db.Repo(the_db.conn, "dir", Dir, ["name"])
            repo.save(Dir("foo"))
            self.assertRaises(Exception, repo.load, 1)

    def test_get_or_insert_content(self):
        with TempDir() as tmpdir:
            db_name = os.path.join(tmpdir.name, "files.db")
            the_db = db.Database(db_name, verbose=0)
            content = Content(1024, "hash1", "hash2", "hash3")
            self.assertEqual(the_db.get_or_insert_content(content), 1)

            content = Content(1024, "hash1", "hash2", "hash3")
            self.assertEqual(the_db.get_or_insert_content(content), 1)

    def test_verbose_for_coverage(self):
        with TempDir() as tmpdir:
            db_name = os.path.join(tmpdir.name, "files.db")
            with nostderr():
                db.Database(db_name, verbose=1)
            self.assertTrue(True)

    def test_dir_repo(self):
        with TempDir() as tmpdir:
            db_fn = os.path.join(tmpdir.name, 'files.db')
            repo = db.Database(db_fn, verbose=0).dir

            obj1 = Dir("foo")
            self.assertEqual(obj1, Dir("foo"))
            repo.save(obj1)
            self.assertEqual(obj1.id, 1)
            self.assertEqual(obj1, Dir("foo", id=1))
            self.assertEqual(repo.load(1), obj1)

            obj2 = Dir("bar")
            repo.save(obj2)
            self.assertEqual(obj2.id, 2)

            self.assert_lists_have_same_items(repo.find_ids(), [1, 2])
            self.assert_lists_have_same_items(repo.find_ids(name="foo"), [1])
            self.assert_lists_have_same_items(repo.find_ids(id=2), [2])
            self.assert_lists_have_same_items(repo.find_ids(name="hello"), [])

            self.assert_lists_have_same_items(repo.find(), [obj1, obj2])
            self.assert_lists_have_same_items(repo.find(name="foo"), [obj1])
            self.assert_lists_have_same_items(repo.find(name="hello"), [])

            obj1.name = "new"
            repo.save(obj1)

            self.assertEqual(repo.load(1), obj1)

            repo.delete(obj1)
            self.assert_lists_have_same_items(repo.find_ids(), [2])

    def test_file_repo(self):
        with TempDir() as tmpdir:
            db_fn = os.path.join(tmpdir.name, 'files.db')
            repo = db.Database(db_fn, verbose=0).file

            obj1 = File(1, "foo", 2, 3)
            self.assertEqual(obj1, File(1, "foo", 2, 3))
            repo.save(obj1)
            self.assertEqual(obj1.id, 1)
            self.assertEqual(obj1, File(1, "foo", 2, 3, id=1))
            self.assertEqual(repo.load(1), obj1)

            obj2 = File(1, "bar", 4, 5)
            repo.save(obj2)
            self.assertEqual(obj2.id, 2)

            obj3 = File(6, "foo", 7, 5)
            repo.save(obj3)
            self.assertEqual(obj3.id, 3)

            self.assert_lists_have_same_items(repo.find_ids(), [1, 2, 3])
            self.assert_lists_have_same_items(repo.find_ids(name="foo"), [1, 3])
            self.assert_lists_have_same_items(repo.find_ids(id=2), [2])
            self.assert_lists_have_same_items(repo.find_ids(dirid=1), [1, 2])
            self.assert_lists_have_same_items(repo.find_ids(contentid=5), [2, 3])
            self.assert_lists_have_same_items(repo.find_ids(name="hello"), [])

            self.assert_lists_have_same_items(repo.find(), [obj1, obj2, obj3])
            self.assert_lists_have_same_items(repo.find(name="foo"), [obj1, obj3])
            self.assert_lists_have_same_items(repo.find(id=2), [obj2])
            self.assert_lists_have_same_items(repo.find(dirid=1), [obj1, obj2])
            self.assert_lists_have_same_items(repo.find(contentid=5), [obj2, obj3])
            self.assert_lists_have_same_items(repo.find(name="hello"), [])

            obj1.name = "new"
            obj1.dirid = 20
            obj1.contentid = 21
            repo.save(obj1)

            self.assertEqual(repo.load(1), obj1)

            repo.delete(obj1)
            self.assert_lists_have_same_items(repo.find_ids(), [2, 3])

    def test_content_repo(self):
        with TempDir() as tmpdir:
            db_fn = os.path.join(tmpdir.name, 'files.db')
            repo = db.Database(db_fn, verbose=0).content

            obj1 = Content(1, "a", "b", "c")
            self.assertEqual(obj1, Content(1, "a", "b", "c"))
            repo.save(obj1)
            self.assertEqual(obj1.id, 1)
            self.assertEqual(obj1, Content(1, "a", "b", "c", id=1))
            self.assertEqual(repo.load(1), obj1)

            obj2 = Content(2, "a", "d", "e")
            repo.save(obj2)
            self.assertEqual(obj2.id, 2)

            obj3 = Content(1, "f", "g", "e")
            repo.save(obj3)
            self.assertEqual(obj3.id, 3)

            self.assert_lists_have_same_items(repo.find_ids(), [1, 2, 3])
            self.assert_lists_have_same_items(repo.find_ids(size=1), [1, 3])
            self.assert_lists_have_same_items(repo.find_ids(id=2), [2])
            self.assert_lists_have_same_items(repo.find_ids(fullsha1="a"), [1, 2])
            self.assert_lists_have_same_items(repo.find_ids(partsha1s="e"), [2, 3])
            self.assert_lists_have_same_items(repo.find_ids(size=99), [])

            self.assert_lists_have_same_items(repo.find(), [obj1, obj2, obj3])
            self.assert_lists_have_same_items(repo.find(size=1), [obj1, obj3])
            self.assert_lists_have_same_items(repo.find(id=2), [obj2])
            self.assert_lists_have_same_items(repo.find(fullsha1="a"), [obj1, obj2])
            self.assert_lists_have_same_items(repo.find(partsha1s="e"), [obj2, obj3])
            self.assert_lists_have_same_items(repo.find(size=99), [])

            obj1.size = 20
            obj1.fullsha1 = "x"
            obj1.first1ksha1 = "y"
            obj1.partsha1sfullsha1 = "z"
            repo.save(obj1)

            self.assertEqual(repo.load(1), obj1)

            repo.delete(obj1)
            self.assert_lists_have_same_items(repo.find_ids(), [2, 3])


if __name__ == '__main__':
    unittest.main()

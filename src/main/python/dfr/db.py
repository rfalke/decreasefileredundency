
import os
import sqlite3
import errno
import sys


from dfr.model import Dir, File, Content, Image


def makedirs(dirname):
    if dirname:
        try:
            os.makedirs(dirname)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        assert os.path.isdir(dirname)


class Null:
    def __init__(self):
        pass


class In:
    def __init__(self, values):
        assert (isinstance(values, (list, tuple)) and
                not isinstance(values, basestring))
        self.values = values


class SelectBuilder:
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns
        self.where_pairs = []
        self.sql = None
        self.order = None

    def add_where(self, cond, *values):
        self.where_pairs.append((cond, values))

    def set_sql(self, sql):
        assert self.sql is None and sql is not None
        self.sql = sql

    def to_sql(self):
        if self.sql:
            return self.sql
        conds = [x[0] for x in self.where_pairs]
        if conds:
            where = " WHERE "+" AND ".join(conds)
        else:
            where = ""
        if self.order:
            order = "ORDER BY "+self.order
        else:
            order = ""
        sql = 'SELECT %s FROM %s %s %s' % (
            self.columns, self.table, where, order)
        return sql

    def get_args(self):
        res = []
        for _, values in self.where_pairs:
            res += values
        return res


class Repo:
    def __init__(self, conn, table, clazz, attrs):
        self.conn = conn
        self.table = table
        self.attrs = attrs
        self.clazz = clazz

    def _execute(self, sql, parameter=None):
        if 0:
            print "Execute %r with parameter=%r" % (sql, parameter)
        try:
            return self.conn.execute(sql, parameter)
        except:
            sys.stderr.write("Error: sql=%r with parameter=%r\n" %
                             (sql, parameter))
            raise

    def save(self, obj):
        assert isinstance(obj, self.clazz)
        cols = ",".join(self.attrs)
        values = [getattr(obj, x) for x in self.attrs]

        if obj.id is None:
            qmarks = ",".join(["?" for x in self.attrs])
            cursor = self._execute(
                'INSERT INTO %s (id,%s) VALUES (NULL, %s)' % (
                self.table, cols, qmarks), values)
            id = cursor.lastrowid
            assert id
            obj.id = id
        else:
            assigns = ["%s=?" % x for x in self.attrs]
            assigns = ",".join(assigns)
            cursor = self._execute('UPDATE %s SET %s WHERE id=?' %
                                   (self.table, assigns),
                                   values+[obj.id])
            assert cursor.rowcount == 1

    def build_where(self, query, builder):
        if "sort" in query:
            value = query["sort"]
            builder.order = value
            del query["sort"]

        for attr in ["id"]+self.attrs:
            if attr in query:
                value = query[attr]
                if isinstance(value, Null) or value == Null:
                    builder.add_where(attr + " IS NULL")
                elif isinstance(value, In):
                    values = value.values
                    qmarks = ','.join('?'*len(values))
                    builder.add_where(attr + " IN (%s)" % qmarks, *values)
                else:
                    builder.add_where(attr + "=?", value)
                del query[attr]

    def _execute_select(self, columns, query):
        builder = SelectBuilder(self.table, columns)
        self.build_where(query, builder)
        return self._execute(builder.to_sql(), builder.get_args())

    def find_ids(self, **query):
        cursor = self._execute_select("id", query)
        res = cursor.fetchall()
        if res:
            return [x[0] for x in res]
        return []

    def find(self, **query):
        cols = ",".join(["id"]+self.attrs)
        cursor = self._execute_select(cols, query)
        res = cursor.fetchall()
        if res:
            objs = [self.construct(x) for x in res]
            for obj in objs:
                assert isinstance(obj, self.clazz)
            return objs

        return []

    def load(self, id):
        objs = self.find(id=id)
        assert len(objs) == 1
        return objs[0]

    def delete(self, obj):
        assert isinstance(obj, self.clazz)
        assert obj.id
        cursor = self._execute("DELETE FROM %s WHERE id = ?" %
                               self.table, [obj.id])
        assert cursor.rowcount == 1
        obj.id = "object deleted in database"

    def construct(self, values):
        raise Exception("Overwrite me to construct for %r %r" % (
            values, self == values))


class DirRepo(Repo):
    def __init__(self, conn):
        Repo.__init__(self, conn, "dir", Dir, ["name"])

    def build_where(self, query, builder):
        Repo.build_where(self, query, builder)
        assert len(query) == 0

    def construct(self, values):
        id, name = values
        return Dir(name, id=id)


class FileRepo(Repo):
    def __init__(self, conn):
        Repo.__init__(self, conn, "file", File,
                      ["dirid", "name", "mtime", "contentid"])

    def build_where(self, query, builder):
        Repo.build_where(self, query, builder)
        assert len(query) == 0

    def construct(self, values):
        id, dirid, name, mtime, contentid = values
        return File(dirid, name, mtime, contentid, id=id)


class ContentRepo(Repo):
    def __init__(self, conn):
        Repo.__init__(self, conn, "content", Content,
                      ["size", "fullsha1", "first1ksha1",
                       "partsha1s", "imageid"])

    def build_where(self, query, builder):
        if "at_least_referenced" in query:
            assert builder.columns == "id"
            at_least = int(query["at_least_referenced"])
            builder.set_sql("SELECT contentid " +
                            "FROM file " +
                            "GROUP BY contentid " +
                            "HAVING COUNT(id) >= %d" % at_least)
            del query["at_least_referenced"]
        elif "at_least_referenced_first1k" in query:
            assert builder.columns == "id"
            at_least = int(query["at_least_referenced_first1k"])
            builder.set_sql("SELECT first1ksha1 " +
                            "FROM content " +
                            "GROUP BY first1ksha1 " +
                            "HAVING COUNT(first1ksha1) >= %d" % at_least)
            del query["at_least_referenced_first1k"]
        else:
            Repo.build_where(self, query, builder)

        assert len(query) == 0

    def construct(self, values):
        id, size, fullsha1, first1ksha1, partsha1s, imageid = values
        return Content(size, fullsha1, first1ksha1, partsha1s, imageid, id=id)


class ImageRepo(Repo):
    def __init__(self, conn):
        Repo.__init__(self, conn, "image", Image,
                      ["sig1", "sig2"])

    def build_where(self, query, builder):
        Repo.build_where(self, query, builder)
        assert len(query) == 0, query

    def construct(self, values):
        id, sig1, sig2 = values
        return Image(sig1, sig2, id=id)


class Database:
    def __init__(self, db_file="files.db", verbose=1):
        do_init = not os.path.exists(db_file)
        makedirs(os.path.dirname(db_file))
        self.conn = sqlite3.connect(db_file)
        self.conn.text_factory = str
        self.dir = DirRepo(self.conn)
        self.file = FileRepo(self.conn)
        self.content = ContentRepo(self.conn)
        self.image = ImageRepo(self.conn)

        if do_init:
            if verbose:
                sys.stderr.write("Creating new database '%s'\n" % db_file)
            self.conn.execute('''
CREATE TABLE dir (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  UNIQUE (name)
)''')
            self.conn.execute('''
CREATE TABLE file (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dirid INTEGER NOT NULL,
  name TEXT NOT NULL,
  contentid INTEGER NOT NULL,
  mtime INTEGER NOT NULL,
  UNIQUE (dirid, name)
)''')
            self.conn.execute('''
CREATE TABLE content (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first1ksha1 TEXT NOT NULL,
  fullsha1 TEXT NOT NULL,
  size INTEGER NOT NULL,
  partsha1s TEXT NOT NULL,
  imageid INTEGER NULL,
  UNIQUE (fullsha1,size)
)''')
            self.conn.execute('''
CREATE TABLE image (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sig1 TEXT NOT NULL,
  sig2 TEXT NOT NULL
)''')
            self.conn.execute('''
CREATE INDEX file_contentid ON FILE (
  contentid
)''')

    def begin(self):
        pass

    def commit(self):
        self.conn.commit()

    def get_or_insert_dir(self, dirname):
        ids = self.dir.find_ids(name=dirname)
        if ids:
            return ids[0]
        else:
            obj = Dir(dirname)
            self.dir.save(obj)
            return obj.id

    def get_or_insert_content(self, obj):
        ids = self.content.find_ids(fullsha1=obj.fullsha1)
        if ids:
            assert len(ids) == 1
            return ids[0]
        else:
            self.content.save(obj)
            return obj.id

    def get_file(self, dirid, filename):
        objs = self.file.find(dirid=dirid, name=filename)
        if objs:
            assert len(objs) == 1
            return objs[0]
        else:
            return None

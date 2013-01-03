
import os,sqlite3

class File:
    pass

class Database:
    def __init__(self, db_file="files.db",verbose=1):
        do_init=not os.path.exists(db_file)
        self.conn = sqlite3.connect(db_file)
        if do_init:
            if verbose:
                print "Creating new database '%s'"%db_file
            self.conn.execute('''
CREATE TABLE dir (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name text NOT NULL,
  UNIQUE (name)
)''')
            self.conn.execute('''
CREATE TABLE file (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dirid INTEGER NOT NULL,
  name TEXT NOT NULL,
  contentid INTEGER NOT NULL,
  UNIQUE (dirid, name)
)''')
            self.conn.execute('''
CREATE TABLE content (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first1ksha1 TEXT NOT NULL,
  fullsha1 TEXT NOT NULL,
  size INTEGER NOT NULL,
  partsha1s TEXT NOT NULL,
  UNIQUE (fullsha1,size)
)''')
            
    def get_or_insert_dir(self, dirname):
        res=self.conn.execute('SELECT id FROM dir WHERE name=?', [dirname]).fetchone()
        if res:
            return res[0]
        else:
            c=self.conn.execute('INSERT INTO dir VALUES (NULL, ?)', [dirname])
            id=c.lastrowid
            assert id
            return id
        
    def get_or_insert_content(self, first_1k_sha1, full_sha1, size, other_sha1s):
        res=self.conn.execute('SELECT id FROM content WHERE fullsha1=?', [full_sha1]).fetchone()
        if res:
            return res[0]
        else:
            c=self.conn.execute('INSERT INTO content VALUES (NULL, ?,?,?,?)', [first_1k_sha1, full_sha1, size, other_sha1s])
            id=c.lastrowid
            assert id
            return id
        
    def insert_or_update_file(self,dirid,filename,contentid):
        c=self.conn.execute('INSERT OR REPLACE INTO file VALUES (NULL, ?,?,?)', [dirid,filename,contentid])

        id=c.lastrowid
        assert id
        return id

    def get_file(self, dirid, filename):
        rs=self.conn.execute('SELECT file.id,content.size FROM file,content WHERE dirid=? and name=? and file.contentid=content.id',
                             [dirid, filename]).fetchone()
        if rs:
            result=File()
            result.size=rs[1]
            result.id=rs[0]
            return result
        return None

    def get_file_names_of_dir(self,dirid):
        return [x[0] for x in self.conn.execute('SELECT name FROM file WHERE dirid=?', [dirid]).fetchall()]

    def remove_file(self,dirid,filename):
        self.conn.execute('DELETE FROM file WHERE dirid=? AND name=?', [dirid,filename])
        
    def begin(self):
        pass

    def commit(self):
        self.conn.commit()        

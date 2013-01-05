
import os, sys
from dfr.bit_hashing import get_sha1sums
from dfr.model import File, Content

MIN_LENGTH = 1024

def abspath(path):
    return os.path.realpath(os.path.abspath(path))

def should_index_file(size):
    return size >= MIN_LENGTH

class BitIndexer:
    def __init__(self, db, verbose_progress=1):
        self.db = db
        self.verbose_progress = verbose_progress

    def run(self, roots):
        for root in roots:
            for dirpath, dirnames, filenames in os.walk(root):
                self.index_one_directory(dirpath, dirnames, filenames)
        self.progress("\n")
    
    def get_or_insert_content(self, fullpath, size):
        first, full, other = get_sha1sums(fullpath, size, MIN_LENGTH)
        other_hashs = " ".join(["%d:%s"%x for x in other.items()])
        obj = Content(size, full, first, other_hashs)
        return self.db.get_or_insert_content(obj)

    def get_file_state(self, dirid, filename, mtime):
        fileobj = self.db.get_file(dirid, filename)
        if not fileobj:
            return "new", File(dirid, filename, mtime, None)
        if fileobj.mtime != mtime:
            return "changed", fileobj
        return "unchanged", fileobj

    # pylint: disable=W0613
    def index_one_directory(self, dirpath, dirnames, filenames):
        self.progress("[")

        self.db.begin()

        dirid = self.db.get_or_insert_dir(abspath(dirpath))

        for fileobj in self.db.file.find(dirid=dirid):
            if fileobj.name not in filenames:
                self.progress("d")
                self.db.file.delete(fileobj)

        for filename in filenames:
            fullpath = os.path.join(dirpath, filename)
            stats = os.stat(fullpath)
            size = long(stats.st_size)
            mtime = int(stats.st_mtime)

            if not should_index_file(size):
                continue
            state, fileobj = self.get_file_state(dirid, filename, mtime)
            if state == "unchanged":
                continue
            elif state == "new":
                self.progress(".")
            else:
                self.progress("m")
                
            contentid = self.get_or_insert_content(fullpath, size)
            fileobj.contentid = contentid
            fileobj.mtime = mtime
            self.db.file.save(fileobj)

        self.db.commit()
        self.progress("]")

    def progress(self, msg):
        if self.verbose_progress:
            sys.stdout.write(msg)
            sys.stdout.flush()

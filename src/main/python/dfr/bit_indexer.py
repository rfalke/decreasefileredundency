
import os
import sys
import errno
import stat
import time
import re

from dfr.bit_hashing import get_sha1sums
from dfr.model import File, Content
from dfr.support import abspath

MIN_LENGTH = 1024


def should_index_file(size):
    return size >= MIN_LENGTH


def remove_excluded_names(names, exclude_comp_re):
    removed = 0
    i = 0
    while i < len(names):
        name = names[i]
        if exclude_comp_re.match(name):
            del names[i]
            removed += 1
        else:
            i += 1
    return removed


class BitIndexer:
    # pylint: disable=R0913
    def __init__(self, db, file_excludes_as_re, dir_excludes_as_re,
                 verbose_progress=2, commit_every=12):
        self.db = db
        self.compiled_file_excludes = re.compile(file_excludes_as_re)
        self.compiled_dir_excludes = re.compile(dir_excludes_as_re)
        self.commit_every = commit_every
        self.verbose_progress = verbose_progress
        self.next_commit = None

    def run(self, roots):
        self.next_commit = time.time() + self.commit_every
        self.progress("Legend: .=new, m=modified, d=deleted, " +
                      "P=permission problem, E=some unknown error\n", 2)
        for root in roots:
            for dirpath, dirnames, filenames in os.walk(root):
                self.index_one_directory(dirpath, dirnames, filenames)
        self.db.commit()
        self.progress("\n")

    def get_or_insert_content(self, fullpath, size):
        first, full, other, is_image = get_sha1sums(fullpath, size, MIN_LENGTH)
        other_hashs = " ".join(["%d:%s" % x for x in other.items()])
        if is_image:
            imageid = None
        else:
            imageid = -1
        obj = Content(size, full, first, other_hashs, imageid)
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
        current_time = time.time()
        if current_time > self.next_commit:
            self.next_commit = current_time + self.commit_every
            self.db.commit()

        dirnames.sort()
        filenames.sort()
        remove_excluded_names(filenames, self.compiled_file_excludes)
        remove_excluded_names(dirnames, self.compiled_dir_excludes)
        self.progress("[")

        self.db.begin()

        dirid = self.db.get_or_insert_dir(abspath(dirpath))

        for fileobj in self.db.file.find(dirid=dirid):
            if fileobj.name not in filenames:
                self.progress("d")
                self.db.file.delete(fileobj)

        for filename in filenames:
            fullpath = os.path.join(dirpath, filename)
            stats = os.lstat(fullpath)
            size = long(stats.st_size)
            mtime = int(stats.st_mtime)

            if not stat.S_ISREG(stats.st_mode):
                continue

            if not should_index_file(size):
                continue
            state, fileobj = self.get_file_state(dirid, filename, mtime)
            if state == "unchanged":
                continue

            try:
                contentid = self.get_or_insert_content(fullpath, size)
                fileobj.contentid = contentid
                fileobj.mtime = mtime
                self.db.file.save(fileobj)

                if state == "new":
                    self.progress(".")
                else:
                    self.progress("m")
            except IOError as exception:
                if exception.errno == errno.EACCES:
                    self.progress("P")
                else:
                    self.progress("E")
        self.progress("]")

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

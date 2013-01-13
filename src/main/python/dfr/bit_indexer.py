
import os
import sys
import errno
import stat
import time
import re
import locale

from dfr.bit_hashing import get_sha1sums
from dfr.model import File, Content
from dfr.support import abspath, format_time_delta, format_bytes_split

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
                 verbose_progress=3, commit_every=12, full_stats_every=30,
                 dir_warn_threshold=3):
        self.db = db
        self.compiled_file_excludes = re.compile(file_excludes_as_re)
        self.compiled_dir_excludes = re.compile(dir_excludes_as_re)
        self.commit_every = commit_every
        self.full_stats_every = full_stats_every
        self.verbose_progress = verbose_progress
        self.dir_warn_threshold = dir_warn_threshold
        self.next_commit = None
        self.next_full_stats = None
        self.start_time = None

        self.dirs_visited = 0
        self.skipped_non_regular_files = 0
        self.skipped_small_files = 0
        self.skipped_dirs = 0
        self.skipped_files = 0
        self.mtime_unchanged_files = 0
        self.deleted_files = 0
        self.new_files = 0
        self.modified_files = 0
        self.read_errors = 0
        self.hashed_bytes = 0
        self.examined_bytes = 0

    def run(self, roots):
        current_time = time.time()
        self.start_time = current_time
        self.next_commit = current_time + self.commit_every
        self.next_full_stats = current_time + self.full_stats_every
        self.progress("Legend: .=new, m=modified, d=deleted, " +
                      "P=permission problem, E=some unknown error\n", 2)
        for root in roots:
            for dirpath, dirnames, filenames in os.walk(root):
                self.index_one_directory(dirpath, dirnames, filenames)
        self.db.commit()
        if self.verbose_progress < 3:
            self.progress("\n")
        self.show_full_stats("Final stats")
        self.progress("Used time: %s\n" %
                      format_time_delta(time.time()-self.start_time), 3)

    def show_full_stats(self, msg):
        self.progress("\n", 3)

        def fmt(number):
            return locale.format("%d", number, 1)
        self.progress(msg+":\n", 3)
        self.progress("       %16s dirs visited\n" % fmt(self.dirs_visited), 3)
        self.progress("       %16s read errors\n" % fmt(self.read_errors), 3)
        self.progress("       %16s skipped directories based on name\n" %
                      fmt(self.skipped_dirs), 3)
        self.progress("       %16s skipped files based on name\n" %
                      fmt(self.skipped_files), 3)
        self.progress("       %16s skipped non regular files\n" %
                      fmt(self.skipped_non_regular_files), 3)

        self.progress("       %16s skipped non regular files\n" %
                      fmt(self.skipped_non_regular_files), 3)
        self.progress("       %16s skipped small files\n" %
                      fmt(self.skipped_small_files), 3)
        self.progress("       %16s unchanged files \n" %
                      fmt(self.mtime_unchanged_files), 3)
        self.progress("       %16s deleted files\n" %
                      fmt(self.deleted_files), 3)
        self.progress("       %16s new files\n" % fmt(self.new_files), 3)
        self.progress("       %16s files with different content\n" %
                      fmt(self.modified_files), 3)
        self.progress("       %16s %s bytes hashed\n" %
                      (format_bytes_split(self.hashed_bytes)), 3)
        total_bytes = self.hashed_bytes+self.examined_bytes
        self.progress("       %16s %s bytes known total\n" %
                      (format_bytes_split(total_bytes)), 3)

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
        if self.full_stats_every and current_time > self.next_full_stats:
            self.next_full_stats = current_time + self.full_stats_every
            runtime = time.time()-self.start_time
            self.show_full_stats("Stats after %s %s" %
                                 (format_time_delta(runtime), dirpath))

        if current_time > self.next_commit:
            self.next_commit = current_time + self.commit_every
            self.db.commit()

        self.dirs_visited += 1
        dirnames.sort()
        filenames.sort()
        self.skipped_files += remove_excluded_names(
            filenames, self.compiled_file_excludes)
        self.skipped_dirs += remove_excluded_names(
            dirnames, self.compiled_dir_excludes)
        self.progress("[")

        self.db.begin()

        dirid = self.db.get_or_insert_dir(abspath(dirpath))

        for fileobj in self.db.file.find(dirid=dirid):
            if fileobj.name not in filenames:
                self.progress("d")
                self.db.file.delete(fileobj)
                self.deleted_files += 1

        start = time.time()
        for filename in filenames:
            if start and time.time() > start+self.dir_warn_threshold:
                self.progress(" %s " % dirpath)
                start = None

            self.index_one_file(dirpath, filename, dirid)
        self.progress("]")

    def index_one_file(self, dirpath, filename, dirid):
        fullpath = os.path.join(dirpath, filename)
        stats = os.lstat(fullpath)
        size = long(stats.st_size)
        mtime = int(stats.st_mtime)

        if not stat.S_ISREG(stats.st_mode):
            self.skipped_non_regular_files += 1
            return

        if not should_index_file(size):
            self.skipped_small_files += 1
            return

        state, fileobj = self.get_file_state(dirid, filename, mtime)
        if state == "unchanged":
            self.mtime_unchanged_files += 1
            self.examined_bytes += size
            return

        try:
            contentid = self.get_or_insert_content(fullpath, size)
            fileobj.contentid = contentid
            fileobj.mtime = mtime
            self.db.file.save(fileobj)
            self.hashed_bytes += size

            if state == "new":
                self.progress(".")
                self.new_files += 1
            else:
                self.progress("m")
                self.modified_files += 1
        except IOError as exception:
            self.read_errors += 1
            if exception.errno == errno.EACCES:
                self.progress("P")
            else:
                self.progress("E")

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

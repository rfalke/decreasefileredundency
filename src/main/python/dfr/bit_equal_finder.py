import os

from dfr.db import In
from dfr.support import abspath, chunker
from dfr.progress import Progress


def compare_files(file1, file2):
    diff = cmp(file1.dirname, file2.dirname)
    if not diff:
        diff = cmp(file1.path, file2.path)
    return diff


def is_known_file(files, file):
    for i in files:
        if os.path.samefile(file.path, i.path):
            return True
    return False


class BitEqualFilePair(object):
    # pylint: disable=R0913
    def __init__(self, size, hardlinked, path1, path2,
                 ctxt_index, ctxt_size, ctxt_subindex):
        self.size = size
        self.hardlinked = hardlinked
        self.path1 = path1
        self.path2 = path2
        self.ctxt_index = ctxt_index
        self.ctxt_size = ctxt_size
        self.ctxt_subindex = ctxt_subindex


class BitEqualBucket(object):
    # pylint: disable=R0913
    def __init__(self, size, files, is_first):
        self.size = size
        self.files = files
        self.is_first = is_first


class BaseFinder(object):
    def __init__(self, db, roots):
        self.db = db
        self.roots = [abspath(x) for x in roots]

    def _is_under_one_of_roots(self, path):
        for root in self.roots:
            if path.startswith(root):
                return True
        return False

    def _find_files_for_content_id(self, contentid):
        files = self.db.file.find(contentid=contentid)

        for file in files:
            dir = self.db.dir.load(file.dirid)
            file.path = os.path.join(dir.name, file.name)
            file.dirname = dir.name

        files = [x for x in files if self._is_under_one_of_roots(x.path)]
        files = [x for x in files if os.path.isfile(x.path)]

        files.sort(compare_files)
        return files


class BitEqualFinder(BaseFinder):
    def __init__(self, db, roots):
        BaseFinder.__init__(self, db, roots)

    def _find_multiple_referenced_content(self):
        ids = self.db.content.find_ids(at_least_referenced=2)
        contents = []
        for ids_part in chunker(ids, 100):
            contents += self.db.content.find(id=In(ids_part))
        contents.sort(lambda x, y: cmp(y.size, x.size))
        return contents

    def find(self):
        contents = self._find_multiple_referenced_content()

        for content_index in range(len(contents)):
            content = contents[content_index]
            files = self._find_files_for_content_id(content.id)

            pair_index = 0
            for i in range(len(files)):
                outer = files[i]
                for j in range(i + 1, len(files)):
                    inner = files[j]
                    if True and (os.path.isfile(outer.path) and
                                 os.path.isfile(inner.path)):
                        yield BitEqualFilePair(
                            content.size,
                            os.path.samefile(outer.path, inner.path),
                            outer.path,
                            inner.path,
                            content_index,
                            len(contents),
                            pair_index)
                        pair_index += 1


class BitEqualBucketFinder(BaseFinder):
    def __init__(self, db, roots):
        BaseFinder.__init__(self, db, roots)

    def _find_multiple_referenced_content(self):
        ids = self.db.content.find_ids(at_least_referenced=2)
        contents = []
        for ids_part in chunker(ids, 100):
            contents += self.db.content.find(id=In(ids_part))
        contents.sort(lambda x, y: cmp(y.size, x.size))
        return contents

    def find(self):
        prog = Progress(1, "Searching for duplicated files", do_output=1)
        contents = self._find_multiple_referenced_content()
        prog.work()
        prog.finish()
        is_first = True

        prog = Progress(len(contents), "Output", do_output=1)
        for content_index in range(len(contents)):
            content = contents[content_index]
            all_files = self._find_files_for_content_id(content.id)
            files = []
            for file in all_files:
                if not is_known_file(files, file):
                    files.append(file)

            if len(files) > 1:
                yield BitEqualBucket(
                    content.size,
                    files, is_first)
                is_first = False
            prog.work()
        prog.finish()

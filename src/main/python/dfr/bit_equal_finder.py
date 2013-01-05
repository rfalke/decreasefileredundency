
import os


def abspath(path):
    return os.path.realpath(os.path.abspath(path))


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))


class Context:
    def __init__(self, index, size, subindex):
        self.index = index
        self.size = size
        self.subindex = subindex


def compare_files(file1, file2):
    diff = cmp(file1.dirname, file2.dirname)
    if not diff:
        diff = cmp(file1.path, file2.path)
    return diff


class BitEqualFinder:
    def __init__(self, db):
        self.db = db

    def _find_multiple_referenced_content(self):
        ids = self.db.content.find_ids(at_least_referenced=2)
        contents = []
        for ids_part in chunker(ids, 100):
            contents += self.db.content.find(id=ids_part)
        contents.sort(lambda x, y: cmp(y.size, x.size))
        return contents

    def _find_files_for_content(self, content, test_func):
        files = self.db.file.find(contentid=content.id)

        for file in files:
            dir = self.db.dir.load(file.dirid)
            file.path = os.path.join(dir.name, file.name)
            file.dirname = dir.name

        files = [x for x in files if test_func(x.path)]
        files = [x for x in files if os.path.isfile(x.path)]

        files.sort(compare_files)
        return files

    def find(self, roots):
        roots = [abspath(x) for x in roots]

        def is_under_one_of_roots(path):
            for root in roots:
                if path.startswith(root):
                    return True
            return False

        contents = self._find_multiple_referenced_content()

        for content_index in range(len(contents)):
            content = contents[content_index]
            files = self._find_files_for_content(content,
                                                 is_under_one_of_roots)

            pair_index = 0
            for i in range(len(files)):
                outer = files[i]
                for j in range(i+1, len(files)):
                    inner = files[j]
                    if True and (os.path.isfile(outer.path) and
                                 os.path.isfile(inner.path)):
                        context = Context(content_index,
                                          len(contents),
                                          pair_index)
                        yield (content.size,
                               os.path.samefile(outer.path, inner.path),
                               outer.path,
                               inner.path,
                               context)
                        pair_index += 1

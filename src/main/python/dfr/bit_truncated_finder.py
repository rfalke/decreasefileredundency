
import os

from dfr.bit_hashing import get_partial_sha1
from dfr.bit_equal_finder import BaseFinder


def small_is_truncated_of_large(large, small):
    large_hashs = large.get_part_hashs()
    small_hashs = small.get_part_hashs()

    size = 2048L
    while True:
        if size not in large_hashs or size not in small_hashs:
            equal_so_far = 1
            size /= 2
            break
        if large_hashs[size] != small_hashs[size]:
            equal_so_far = 0
            break
        size *= 2
    if not equal_so_far:
        return False

    smaller_full_hash = small.fullsha1
    larger_hash_till_size_of_small = get_partial_sha1(
        large.files[0].path, 0, small.size)

    if smaller_full_hash != larger_hash_till_size_of_small:
        return False

    return True


class Context:
    def __init__(self, index, size, subindex):
        self.index = index
        self.size = size
        self.subindex = subindex


class TruncatedFile:
    # pylint: disable=R0913
    def __init__(self, large_size, large_path, small_size, small_path,
                 ctxt_index, ctxt_size, ctxt_subindex):
        self.large_size = large_size
        self.large_path = large_path
        self.small_size = small_size
        self.small_path = small_path
        self.ctxt_index = ctxt_index
        self.ctxt_size = ctxt_size
        self.ctxt_subindex = ctxt_subindex


def output_pair(large, small, context):
    large_filenames = [x.path for x in large.files]
    small_filenames = [x.path for x in small.files]

    for lfn in large_filenames:
        for sfn in small_filenames:
            if True and (os.path.isfile(lfn) and
                         os.path.isfile(sfn)):
                yield TruncatedFile(large.size, lfn, small.size, sfn,
                                    context.index, context.size,
                                    context.subindex)


class BitTruncatedFinder(BaseFinder):
    def __init__(self, db, roots):
        BaseFinder.__init__(self, db, roots)

    def find(self):
        first1k_sha1s = self.db.content.find_ids(at_least_referenced_first1k=2)
        first1k_sha1s = sorted(first1k_sha1s)

        context = Context(0, len(first1k_sha1s), 0)
        for hash_index in range(len(first1k_sha1s)):
            hash = first1k_sha1s[hash_index]
            context.index = hash_index
            context.subindex = 0

            contents = self.db.content.find(first1ksha1=hash)
            assert len(contents) >= 2
            for content in contents:
                content.files = self._find_files_for_content_id(content.id)

            contents = [x for x in contents if x.files]
            if len(contents) < 2:
                continue
            contents.sort(lambda x, y: cmp(y.size, x.size))

            for i in range(len(contents)):
                outer = contents[i]
                for j in range(i+1, len(contents)):
                    inner = contents[j]
                    if outer.size == inner.size:
                        continue
                    assert outer.size > inner.size
                    large, small = outer, inner
                    if small_is_truncated_of_large(large, small):
                        for obj in output_pair(large, small, context):
                            yield obj
                            context.subindex += 1

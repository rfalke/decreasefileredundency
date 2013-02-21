
import sys

from dfr.bit_equal_finder import BaseFinder


class ImageSimiliarFilePair:
    # pylint: disable=R0913
    def __init__(self, similarity, path1, path2,
                 ctxt_index, ctxt_size):
        self.similarity = similarity
        self.path1 = path1
        self.path2 = path2
        self.ctxt_index = ctxt_index
        self.ctxt_size = ctxt_size


def prepare_sig1(hash):
    return [int(x, 16) for x in hash.split(" ")]


def compare_sig1(hash1, hash2):
    if len(hash1) != len(hash2):
        return 0
    error = 0
    for i in range(len(hash1)):
        error += abs(hash1[i] - hash2[i])
    return 1-error / float(2**17)


def prepare_sig2(hash):
    return int(hash, 16)


def compare_sig2(hash1, hash2):
    xor = hash1 ^ hash2
    distance = bin(xor).count("1")
    similarity = 1-distance/256.0
    return similarity


class ImageSimilarFinder(BaseFinder):
    def __init__(self, db, roots, sig_type, verbose_progress=1):
        BaseFinder.__init__(self, db, roots)
        self.verbose_progress = verbose_progress
        assert sig_type in [1, 2]
        self.iht = sig_type
        if sig_type == 1:
            self.prepare = prepare_sig1
            self.compare = compare_sig1
        else:
            self.prepare = prepare_sig2
            self.compare = compare_sig2
        self.done = None
        self.num_todo = None

    def _find_contents(self):
        contents = self.db.content.find(isimage=1)
        print "looking for files ..."
        for content in contents:
            content.files = []
            hashs = self.db.imagehash.find(contentid=content.id, iht=self.iht)
            if hashs:
                assert len(hashs) == 1
                if hashs[0].hash:
                    content.prepared_hash = self.prepare(hashs[0].hash)
                    content.files = self._find_files_for_content_id(content.id)
        contents = [x for x in contents if x.files]
        print ".. done"
        return contents

    def find(self, min_similarity):
        contents = self._find_contents()
        res = []
        contents.sort(lambda x, y: cmp(x.id, y.id))
        self.num_todo = (len(contents) * (len(contents)-1))/2
        self.done = 0
        for index1 in range(len(contents)):
            content1 = contents[index1]
            for index2 in range(index1+1, len(contents)):
                content2 = contents[index2]
                sim = self.compare(content1.prepared_hash,
                                   content2.prepared_hash)
                if sim >= min_similarity:
                    res.append((sim, index1, index2))
                if self.done % 10000 == 0:
                    self.progress("Comparing %.1f%% %d/%d\r" % (
                        (100.0*self.done)/self.num_todo,
                        self.done/10000,
                        self.num_todo/10000))
                self.done += 1
        res.sort(reverse=True)
        self.progress("\r%s\r" % " "*30)

        for index in range(len(res)):
            similarity, index1, index2 = res[index]
            file1 = contents[index1].files[0].path
            file2 = contents[index2].files[0].path
            yield ImageSimiliarFilePair(similarity, file1, file2,
                                        index, len(res))

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

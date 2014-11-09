
import sys

from dfr.bit_equal_finder import BaseFinder
from dfr.model import ImageFeedback
from dfr.progress import Progress


class ImageSimiliarFilePair(object):
    # pylint: disable=R0913
    def __init__(self, similarity, path1, path2,
                 ctxt_index, ctxt_size, db,
                 content_id1, content_id2):
        self.similarity = similarity
        self.path1 = path1
        self.path2 = path2
        self.ctxt_index = ctxt_index
        self.ctxt_size = ctxt_size
        self.db = db
        self.content_id1 = content_id1
        self.content_id2 = content_id2

    def get_feedback(self):
        known = self.db.imagefeedback.find(contentid1=self.content_id1,
                                           contentid2=self.content_id2)
        if known:
            return known[0].aresimilar
        else:
            return None

    def save_feedback(self, are_similar):
        obj = ImageFeedback(self.content_id1, self.content_id2, are_similar)
        self.db.imagefeedback.save(obj, "INSERT OR REPLACE")
        self.db.commit()

    def clear_feedback(self):
        known = self.db.imagefeedback.find(contentid1=self.content_id1,
                                           contentid2=self.content_id2)
        if known:
            self.db.imagefeedback.delete(known[0])
            self.db.commit()


class ImageSimilarFinder(BaseFinder):
    def __init__(self, db, roots, sig_type, verbose_progress=1):
        BaseFinder.__init__(self, db, roots)
        self.verbose_progress = verbose_progress
        assert sig_type in [1, 2, 3, 4, 5]
        self.iht = sig_type
        self.done = None
        self.num_todo = None

    def _find_contents(self):
        contents = self.db.content.find(isimage=1)
        prog = Progress(len(contents), "Searching image files")
        for content in contents:
            content.files = self._find_files_for_content_id(content.id)
            prog.work()
        contents = [x for x in contents if x.files]
        prog.finish()
        return contents

    def load_known(self, min_similarity, content_ids):
        tiles = self.db.imagecmp.find(iht=self.iht)
        res = []
        for tile in tiles:
            assert tile.similarity_threshold <= min_similarity
            for id1, id2, sim in tile.get_decoded_pairs():
                if id1 in content_ids and \
                   id2 in content_ids and \
                   sim >= min_similarity:
                    res.append((sim, id1, id2))
        res.sort(reverse=True)
        return res

    def find(self, min_similarity):
        contents = self._find_contents()
        contents.sort(lambda x, y: cmp(x.id, y.id))
        content_by_id = {}
        for i in contents:
            content_by_id[i.id] = i

        res = self.load_known(min_similarity, set(content_by_id.keys()))

        for index in range(len(res)):
            similarity, id1, id2 = res[index]
            content1 = content_by_id[id1]
            content2 = content_by_id[id2]
            file1 = content1.files[0].path
            file2 = content2.files[0].path
            yield ImageSimiliarFilePair(similarity, file1, file2,
                                        index, len(res), self.db,
                                        content1.id, content2.id)

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

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


class ImageSimiliarFileBucket(object):
    # pylint: disable=R0913
    def __init__(self, score, center, others):
        self.score = score
        self.center = center
        self.others = others


class ImageSimilarFinder(BaseFinder):
    def __init__(self, db, roots, sig_type, verbose_progress=1):
        BaseFinder.__init__(self, db, roots)
        self.verbose_progress = verbose_progress
        assert sig_type in [1, 2, 3, 4, 5]
        self.iht = sig_type

    def _find_contents(self):
        contents = self.db.content.find(isimage=1)
        prog = Progress(len(contents), "Searching image files")
        for content in contents:
            content.files = self._find_files_for_content_id(content.id)
            prog.work()
        contents = [x for x in contents if x.files]
        prog.finish()
        return contents

    def find(self, min_similarity):
        contents = self._find_contents()
        contents.sort(lambda x, y: cmp(x.id, y.id))
        content_by_id = {}
        for i in contents:
            content_by_id[i.id] = i
        res = self.db.imagecmp.find(iht=self.iht, sort="score DESC")
        for index in range(len(res)):
            obj = res[index]
            for i in self.handle(obj, content_by_id, min_similarity,
                                 (index, len(res))):
                yield i

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

    def handle(self, obj, content_by_id, min_similarity, position):
        content1 = content_by_id[obj.contentid]
        file1 = content1.files[0].path
        pairs = obj.get_pairs()
        for contentid2, similarity in pairs:
            content2 = content_by_id[contentid2]
            file2 = content2.files[0].path
            if similarity >= min_similarity:
                index, num_findings = position
                yield ImageSimiliarFilePair(similarity, file1, file2,
                                            index, num_findings, self.db,
                                            content1.id, content2.id)


class ImageSimilarBucketFinder(ImageSimilarFinder):
    def __init__(self, db, roots, sig_type, verbose_progress=1):
        ImageSimilarFinder.__init__(self, db, roots, sig_type,
                                    verbose_progress)

    def handle(self, obj, content_by_id, min_similarity, position):
        center = content_by_id[obj.contentid]
        center_paths = [x.path for x in center.files]
        pairs = obj.get_pairs()
        others = []
        for contentid2, similarity in pairs:
            if similarity >= min_similarity:
                other = content_by_id[contentid2]
                other_paths = [x.path for x in other.files]
                others.append((similarity, other_paths))
        if others:
            yield ImageSimiliarFileBucket(obj.score, center_paths, others)

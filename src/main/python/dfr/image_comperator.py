import sys
import subprocess
import os

from dfr.model import ImageCmp
from dfr.progress import Progress
import dfr.model


def prepare_sig1(hash):
    return [int(x, 16) for x in hash.split(" ")]


def prepare_hex_sig(hash):
    return int(hash, 16)


def write_image_hash_data_file(contents, contents_by_id, min_similarity):
    max_dist = int(64 * (1 - min_similarity))
    filename = "images.data"
    file = open(filename, "w")
    last_id = contents[-1].id
    to_output = min(10000, (last_id + 1))
    factors = [str(int(10 * ((13.0 - x) / 2 + 1.5))) for x in range(16)]
    file.write("%d %d %d %s\n" % ((last_id + 1), max_dist, to_output,
                                  " ".join(factors)))
    for id in range(last_id + 1):
        content = contents_by_id.get(id, None)
        if content is not None:
            file.write("%016x\n" % content.prepared_hash)
        else:
            file.write("na\n")
    file.close()
    # print "content hash = " + open(filename).read()
    return filename


def write_image_histo_data_file(contents, contents_by_id, min_similarity):
    def inner(filename, hash_length):
        assert hash_length in [16, 3 * 16]
        words = hash_length / 16
        written = 0
        file = open(filename, "w")
        last_id = contents[-1].id
        to_output = min(10000, (last_id + 1))
        file.write("%d %d %d %d " % ((last_id + 1),
                                     to_output, words,
                                     int(100 * (1 - min_similarity))))
        factors = [str(40 - x) for x in range(32)]
        file.write("%s\n" % (" ".join(factors)))
        for id in range(last_id + 1):
            content = contents_by_id.get(id, None)
            if content is not None:
                assert len(content.prepared_hash) in [16, 3 * 16], \
                    [id, len(content.prepared_hash)]
            available = (content is not None and
                         len(content.prepared_hash) == hash_length)
            if available:
                tmp = []
                for i in content.prepared_hash:
                    i /= 256
                    assert i >= 0 and i <= 255, content.prepared_hash
                    tmp.append("%02x" % i)
                if words == 3:
                    tmp[2 * 16:2 * 16] = [" "]
                    tmp[16:16] = [" "]
                file.write("%s\n" % "".join(tmp))
                written += 1
            else:
                file.write("na\n")
        file.close()
        if written:
            # print "content histo = '%s'" % open(filename).read()
            return [filename]
        else:
            return []

    filename1 = "images_histo_bw.data"
    filename2 = "images_histo_rgb.data"
    return inner(filename1, 16) + inner(filename2, 3 * 16)


class ImageComperator(object):
    def __init__(self, db, sig_type, commit_every=12, verbose_progress=1):
        self.db = db
        self.commit_every = commit_every
        self.verbose_progress = verbose_progress
        assert sig_type in [1, 2, 3, 4, 5]
        self.iht = sig_type
        if sig_type == 1:
            self.prepare = prepare_sig1
        elif sig_type in [2, 3, 4, 5]:
            self.prepare = prepare_hex_sig
        self.base_path = (os.path.abspath(os.path.dirname(dfr.model.__file__)
                                          + "/../../../.."))

    def _find_contents(self):
        prog = Progress(1, "Loading images",
                        do_output=self.verbose_progress > 0)
        contents = self.db.content.find(isimage=1)
        prog.work()
        prog.finish()

        prog = Progress(len(contents), "Loading image hashes",
                        do_output=self.verbose_progress > 0)
        for content in contents:
            content.prepared_hash = None
            hashs = self.db.imagehash.find(contentid=content.id, iht=self.iht)
            if hashs:
                assert len(hashs) == 1
                if hashs[0].hash:
                    content.prepared_hash = self.prepare(hashs[0].hash)
            prog.work()
        contents = [x for x in contents if x.prepared_hash is not None]
        prog.finish()
        return contents

    def read_results_into_db(self, filename, min_similarity):
        # print "histo result = '%s'" % open(filename).read()
        for line in file(filename).readlines():
            # 0: 88 6=2,1,,,2,1,,,,,,,,,, 1:0 2:1 3:4 5:4 6:5 7:0
            id, rest = line.split(":", 1)
            score, counter, pairs = rest.strip().split(" ", 2)
            id = int(id)
            score = int(score)
            counter = int(counter.split("=")[0])
            pairs = pairs.split(" ")
            assert counter == len(pairs)
            self.db.imagecmp.save(ImageCmp(id, self.iht,
                                           min_similarity, score,
                                           len(pairs), " ".join(pairs)))
        self.db.commit()
        os.remove(filename)

    def calculate_differences(self, contents, min_similarity):

        for obj in self.db.imagecmp.find(iht=self.iht):
            self.db.imagecmp.delete(obj)

        contents_by_id = {}
        for i in contents:
            contents_by_id[i.id] = i
        if self.iht in [2, 3, 4, 5]:
            data_fn = write_image_hash_data_file(contents, contents_by_id,
                                                 min_similarity)
            result_fn = "hamming_distances"

            args = [self.base_path + "/target/calc_hamming_distance",
                    data_fn, result_fn]
            if not self.verbose_progress:
                args[1:1] = ["-q"]
            subprocess.check_call(args)
            self.read_results_into_db(result_fn, min_similarity)
            os.remove(data_fn)
        elif self.iht in [1]:
            data_fns = write_image_histo_data_file(contents, contents_by_id,
                                                   min_similarity)
            result_fn = "histogram_distances"
            for data_fn in data_fns:
                args = [self.base_path + "/target/calc_histogram_distance",
                        data_fn, result_fn]
                if not self.verbose_progress:
                    args[1:1] = ["-q"]
                subprocess.check_call(args)
                self.read_results_into_db(result_fn, min_similarity)
                os.remove(data_fn)

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

    def ensure_that_differences_are_calculated(self, min_similarity):
        contents = self._find_contents()
        contents.sort(lambda x, y: cmp(x.id, y.id))

        if contents:
            self.calculate_differences(contents, min_similarity)
        self.progress("INFO: Have compared all image signatures.\n")

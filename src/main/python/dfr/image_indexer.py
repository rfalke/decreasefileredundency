
import os
import sys
import time
import multiprocessing

from dfr.image_hashing import get_image_signature1, get_image_signatures2, \
    get_image_signature3, get_image_signature4, get_image_signature5
from dfr.model import ImageHash
from dfr.progress import Progress
from dfr.support import chunker, format_time_delta


CHUNK_SIZE = 20


def calc_sig1(pairs):
    res = {}
    for contentid, files in pairs:
        filename = files[0]
        try:
            sig = get_image_signature1(filename)
            sig = ["%x" % ((2**16-1)*x) for x in sig]
            sig = " ".join(sig)
            res[contentid] = sig
        except (IOError, AssertionError, TypeError):
            res[contentid] = None
    return res


def calc_sig2(pairs):
    files = [x[1][0] for x in pairs]
    sigs = get_image_signatures2(files)

    res = {}
    for i in range(len(pairs)):
        contentid, files = pairs[i]
        res[contentid] = sigs[i]
    return res


def calc_sig3(pairs):
    res = {}
    for contentid, files in pairs:
        filename = files[0]
        try:
            sig = get_image_signature3(filename)
            sig = '%016x' % sig
            res[contentid] = sig
        except (IOError, AssertionError, TypeError, IndexError):
            res[contentid] = None
    return res


def calc_sig4(pairs):
    res = {}
    for contentid, files in pairs:
        filename = files[0]
        try:
            sig = get_image_signature4(filename)
            sig = '%016x' % sig
            res[contentid] = sig
        except (IOError, AssertionError, TypeError):
            res[contentid] = None
    return res


def calc_sig5(pairs):
    res = {}
    for contentid, files in pairs:
        filename = files[0]
        try:
            sig = get_image_signature5(filename)
            sig = '%016x' % sig
            res[contentid] = sig
        except (IOError, AssertionError, TypeError):
            res[contentid] = None
    return res


def execute_job(job):
    assert job.type in [1, 2, 3, 4, 5]
    start = time.time()
    if job.type == 1:
        sig = calc_sig1(job.pairs)
    elif job.type == 2:
        sig = calc_sig2(job.pairs)
    elif job.type == 3:
        sig = calc_sig3(job.pairs)
    elif job.type == 4:
        sig = calc_sig4(job.pairs)
    elif job.type == 5:
        sig = calc_sig5(job.pairs)
    used = time.time()-start
    return (job.type, sig, used)


class Job(object):
    def __init__(self, type, pairs):
        self.type = type
        self.pairs = pairs


class ImageIndexer(object):
    # pylint: disable=R0913
    def __init__(self, db, signature_types, verbose_progress=2,
                 commit_every=12, parallel_threads=1):
        assert parallel_threads >= 1
        self.db = db
        self.signature_types = signature_types
        self.verbose_progress = verbose_progress
        self.commit_every = commit_every
        if parallel_threads > 1:
            self.pool = multiprocessing.Pool(processes=parallel_threads)
        else:
            self.pool = None
        self.parallel_threads = parallel_threads
        self.next_commit = None
        self.time_per_type = None

    def create_jobs(self, ids):
        jobs = []
        for chunk in chunker(ids, CHUNK_SIZE):
            todo = [(x, self.find_files_for_content(x)) for x in chunk]
            todo = [(id, files) for id, files in todo if files]
            for i in self.signature_types:
                jobs.append(Job(i, todo))
        return jobs

    def execute_jobs(self, jobs):
        if self.pool:
            result = self.pool.map(execute_job, jobs)
        else:
            result = [execute_job(x) for x in jobs]
        for type, _, time_used in result:
            self.time_per_type[type] += time_used
        return result

    def save_results(self, all_results):
        for type, results, _ in all_results:
            for contentid in results:
                sig = results[contentid]
                self.db.imagehash.save(ImageHash(contentid, type, sig))

    def run(self):
        prog = Progress(1, "Determine images without hashes",
                        do_output=self.verbose_progress > 0)

        indexed_ids = set([x.contentid for x in self.db.imagehash.find()])
        tmp = set(self.db.content.find_ids(isimage=1,
                                           sort="first1ksha1 ASC"))
        ids_to_index = list(tmp - indexed_ids)
        prog.work()
        prog.finish()

        if not ids_to_index:
            self.progress("INFO: Have calculated all image signatures.\n")
            return
        prog = Progress(len(ids_to_index), "Calculate image signatures",
                        do_output=self.verbose_progress > 0)
        current_time = time.time()
        self.next_commit = current_time + self.commit_every
        self.time_per_type = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for chunk in chunker(ids_to_index, CHUNK_SIZE * self.parallel_threads):
            current_time = time.time()
            if current_time > self.next_commit:
                self.next_commit = current_time + self.commit_every
                self.db.commit()

            jobs = self.create_jobs(chunk)
            result = self.execute_jobs(jobs)
            self.save_results(result)

            prog.work(len(chunk))
        prog.finish()
        self.db.commit()
        self.report_time_used_per_type()

    def report_time_used_per_type(self):
        for i in [1, 2, 3, 4, 5]:
            time_used = format_time_delta(self.time_per_type[i])
            self.progress("  hash type %d used %s\n" % (i, time_used))

    def prepare(self, files):
        for file in files:
            dir = self.db.dir.load(file.dirid)
            file.path = os.path.join(dir.name, file.name)
        files = [x for x in files if os.path.isfile(x.path)]
        return [x.path for x in files]

    def find_files_for_content(self, contentid):
        files = self.db.file.find(contentid=contentid)
        return self.prepare(files)

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

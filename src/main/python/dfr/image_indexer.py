
import os
import sys
import time
import multiprocessing

from dfr.image_hashing import get_image_signature1, get_image_signatures2, \
    get_image_signature3, get_image_signature4
from dfr.model import ImageHash
from dfr.support import chunker, format_time_delta


CHUNK_SIZE = 20


def calc_sig1(pairs):
    res = {}
    for contentid, files in pairs:
        filename = files[0]
        try:
            sig = get_image_signature1(filename)
            sig = ["%x" % (2**16*x) for x in sig]
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
        except (IOError, AssertionError, TypeError):
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


def execute_job(job):
    assert job.type in [1, 2, 3, 4]
    if job.type == 1:
        return (1, calc_sig1(job.pairs))
    elif job.type == 2:
        return (2, calc_sig2(job.pairs))
    elif job.type == 3:
        return (3, calc_sig3(job.pairs))
    elif job.type == 4:
        return (4, calc_sig4(job.pairs))


class Job:
    def __init__(self, type, pairs):
        self.type = type
        self.pairs = pairs


class ImageIndexer:
    def __init__(self, db, verbose_progress=2, commit_every=12,
                 parallel_threads=1):
        assert parallel_threads >= 1
        self.db = db
        self.verbose_progress = verbose_progress
        self.commit_every = commit_every
        self.num_todo = None
        self.done = None
        self.start = None
        if parallel_threads > 1:
            self.pool = multiprocessing.Pool(processes=parallel_threads)
        else:
            self.pool = None
        self.parallel_threads = parallel_threads
        self.next_commit = None

    def create_jobs(self, ids):
        jobs = []
        for chunk in chunker(ids, CHUNK_SIZE):
            todo = [(x, self.find_files_for_content(x)) for x in chunk]
            todo = [(id, files) for id, files in todo if files]
            jobs.append(Job(1, todo))
            jobs.append(Job(2, todo))
            jobs.append(Job(3, todo))
            jobs.append(Job(4, todo))
        return jobs

    def execute_jobs(self, jobs):
        if self.pool:
            result = self.pool.map(execute_job, jobs)
        else:
            result = [execute_job(x) for x in jobs]
        return result

    def save_results(self, all_results):
        for type, results in all_results:
            for contentid in results:
                sig = results[contentid]
                self.db.imagehash.save(ImageHash(contentid, type, sig))

    def run(self):
        indexed_ids = set([x.contentid for x in self.db.imagehash.find()])
        tmp = set(self.db.content.find_ids(isimage=1,
                                           sort="first1ksha1 ASC"))
        ids_to_index = list(tmp - indexed_ids)

        if not ids_to_index:
            self.progress("INFO: Have calculated all image signatures.\n")
            return
        current_time = time.time()
        self.start = current_time
        self.next_commit = current_time + self.commit_every
        self.num_todo = len(ids_to_index)
        self.done = 0
        for chunk in chunker(ids_to_index, CHUNK_SIZE * self.parallel_threads):
            current_time = time.time()
            if current_time > self.next_commit:
                self.next_commit = current_time + self.commit_every
                self.db.commit()
            self.print_progress()

            jobs = self.create_jobs(chunk)
            result = self.execute_jobs(jobs)
            self.save_results(result)

            self.done += len(chunk)
        self.db.commit()
        self.progress("\n")

    def print_progress(self):
        used = time.time() - self.start
        percent_done = float(self.done)/self.num_todo
        if percent_done:
            total = used / percent_done
        else:
            total = 0
        remain = total * (1-percent_done)
        speed = self.done/(used/60)
        self.progress("%s\r" % (" "*40))
        self.progress("Processed %d/%d in %s [ %d/minute ] [ ETA %s ]\r" % (
            self.done, self.num_todo,
            format_time_delta(used), speed, format_time_delta(remain)))

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

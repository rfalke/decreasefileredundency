
import os
import sys
import time
import multiprocessing

from dfr.image_hashing import get_image_signature1, get_image_signatures2
from dfr.model import Image
from dfr.db import Null
from dfr.support import chunker, format_time_delta


CHUNK_SIZE = 20


def calc_sig1(pairs):
    res = {}
    for contentid, files in pairs:
        filename = files[0]
        try:
            sig1 = get_image_signature1(filename)
            sig1 = ["%x" % (2**16*x) for x in sig1]
            sig1 = " ".join(sig1)
            res[contentid] = sig1
        except IOError:
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


def execute_job(job):
    assert job.type in [1, 2]
    if job.type == 1:
        return (1, calc_sig1(job.pairs))
    elif job.type == 2:
        return (2, calc_sig2(job.pairs))


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
        return jobs

    def execute_jobs(self, jobs):
        if self.pool:
            result = self.pool.map(execute_job, jobs)
        else:
            result = [execute_job(x) for x in jobs]
        return result

    def save_results(self, all_results):
        content_id_to_image = {}
        for type, results in all_results:
            for contentid in results:
                sig = results[contentid]
                if contentid not in content_id_to_image:
                    content_id_to_image[contentid] = Image(None, None)
                assert type in [1, 2]
                if type == 1:
                    content_id_to_image[contentid].sig1 = sig
                elif type == 2:
                    content_id_to_image[contentid].sig2 = sig
        for contentid in content_id_to_image:
            content = self.db.content.load(contentid)
            image = content_id_to_image[contentid]
            if image.sig1 and image.sig2:
                self.db.image.save(image)

                content.imageid = image.id
            else:
                content.imageid = -1
            self.db.content.save(content)

    def run(self):
        ids_to_index = self.db.content.find_ids(imageid=Null,
                                                sort="first1ksha1 ASC")
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


import os
import sys
import time

from dfr.image_hashing import get_image_signature1, get_image_signatures2
from dfr.model import Image
from dfr.db import Null


def format_time_delta(sec):
    sec = int(sec)
    min = sec / 60
    sec = sec % 60
    hour = min / 60
    min = min % 60
    if hour:
        return "%d:%02d:%02d" % (hour, min, sec)
    elif min:
        return "%d:%02d" % (min, sec)
    else:
        return "%ds" % (sec)


class ImageIndexer:
    def __init__(self, db, verbose_progress=2):
        self.db = db
        self.verbose_progress = verbose_progress
        self.todo = None
        self.done = None
        self.start = None

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

    def print_progress(self):
        used = time.time() - self.start
        percent_done = float(self.done)/self.todo
        if percent_done:
            total = used / percent_done
        else:
            total = 0
        remain = total * (1-percent_done)
        speed = self.done/(used/60)
        sys.stdout.write("%s\r" % (" "*40))
        sys.stdout.write("Processed %d/%d in %s [ %d/minute ] [ ETA %s ]\r" % (
            self.done, self.todo,
            format_time_delta(used), speed, format_time_delta(remain)))
        sys.stdout.flush()

    def run(self):
        ids_to_index = self.db.content.find_ids(imageid=Null)
        self.start = time.time()
        self.todo = len(ids_to_index)
        self.done = 0
        for i in range(len(ids_to_index)):
            self.done = i
            self.print_progress()
            if i % 10 == 0:
                self.db.commit()
            contentid = ids_to_index[i]
            content = self.db.content.load(contentid)
            files = self.find_files_for_content(content)
            if files:
                content.imageid = self.create_image(files)
                self.db.content.save(content)
        self.db.commit()
        self.progress("\n")

    def find_files_for_content(self, content):
        files = self.db.file.find(contentid=content.id)

        for file in files:
            dir = self.db.dir.load(file.dirid)
            file.path = os.path.join(dir.name, file.name)
        files = [x for x in files if os.path.isfile(x.path)]

        return [x.path for x in files]

    def create_image(self, filenames):
        filename = filenames[0]
        try:
            sig1 = get_image_signature1(filename)
        except KeyboardInterrupt:
            raise
        except:
            return -1

        try:
            sig2 = get_image_signatures2([filename])[0]
        except KeyboardInterrupt:
            raise
        except:
            return -1
        if not sig2:
            return -1

        sig1 = ["%x" % (2**16*x) for x in sig1]
        sig1 = " ".join(sig1)

        image = Image(sig1, sig2)
        self.db.image.save(image)
        return image.id

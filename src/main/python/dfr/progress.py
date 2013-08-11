
import sys
import time

from dfr.support import format_time_delta

TOTAL_BARS = 40


def format_number(number):
    res = "%4d" % number
    if len(res) > 4:
        res = ">999"
    return res


class Progress:
    def __init__(self, todo, msg, msg_len=None, do_output=1):
        self.do_output = do_output
        self.update_every = 0.5
        self.speed_text = "unknown"
        if msg_len is None:
            msg_len = len(msg)
        self.todo = todo
        self.msg = (msg+(" "*msg_len))[:msg_len]
        self.start_time = time.time()
        self.done = 0
        self.last_update = 0

    def work(self, update=1):
        self.done += update

        if time.time() - self.last_update > self.update_every:
            self.last_update = time.time()
            time_used = time.time() - self.start_time
            percent_done = float(self.done)/self.todo

            if percent_done:
                total_time = time_used / percent_done
            else:
                total_time = 0
            remaining_time = total_time * (1-percent_done)
            speed_per_sec = self.done/time_used
            if int(speed_per_sec) < 4:
                self.speed_text = "%s/min" % format_number(60*speed_per_sec)
            else:
                self.speed_text = "%s/sec" % format_number(speed_per_sec)

            bars = int(percent_done * TOTAL_BARS)

            self.clear_line()
            self.progress("%s: %s%s %5.1f%% in %s [ %s ] [ ETA %8s ]\r" % (
                self.msg, "="*bars, " "*(TOTAL_BARS-bars),
                100*percent_done,
                format_time_delta(time_used), self.speed_text,
                format_time_delta(remaining_time)))

    def finish(self):
        assert self.done == self.todo

        self.clear_line()
        self.progress("%s: %s %d/%d in %s [ %s ]\n" % (
            self.msg, "="*TOTAL_BARS,
            self.done, self.todo,
            format_time_delta(time.time()-self.start_time),
            self.speed_text))

    def clear_line(self):
        self.progress("%s\r" % (" "*120))

    def progress(self, msg):
        if self.do_output:
            sys.stderr.write(msg)
            sys.stderr.flush()

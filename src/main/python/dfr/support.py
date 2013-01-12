
import os
import locale


def abspath(path):
    return os.path.realpath(os.path.abspath(path))


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))


def format_bytes(num):
    locale.setlocale(locale.LC_ALL, 'en_US')
    first = locale.format('%d', num, 1)
    if num < 1024:
        return first

    suffixes = ['KiB', 'MiB', 'GiB', 'TiB']
    suffix = len(suffixes)-1
    for i in range(len(suffixes)):
        num /= 1024.0
        if num < 1024.0:
            suffix = i
            break
    return "%s (%3.1f %s)" % (first, num, suffixes[suffix])


def format_time_delta(sec):
    sec = int(sec)
    min = sec / 60
    sec = sec % 60
    hour = min / 60
    min = min % 60
    day = hour / 24
    hour = hour % 24
    if day:
        return "%dd %dh" % (day, hour)
    if hour:
        return "%dh %dm" % (hour, min)
    elif min:
        return "%dm %ds" % (min, sec)
    else:
        return "%ds" % (sec)

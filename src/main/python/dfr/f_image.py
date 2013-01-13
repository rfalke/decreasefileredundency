#!/usr/bin/env python

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))

import dfr.db
from dfr.image_indexer import ImageIndexer
from dfr.support import add_common_command_line_arguments

DEFAULT_THREADS = "C"


def eval_thread_config(spec):
    try:
        return int(spec)
    except ValueError:
        pass

    if spec.lower().endswith("c"):
        factor = spec[:-1]

        import multiprocessing
        cpus = multiprocessing.cpu_count()
        if factor == "":
            return cpus
        try:
            return int(cpus * float(factor))
        except:
            raise
    assert 0, "Failed to understand thread spec %r" % spec


def main():
    parser = argparse.ArgumentParser(
        description='Generate image signatures for files in database.')
    add_common_command_line_arguments(parser)
    parser.add_argument('-T', '--threads', metavar='THREADS',
                        nargs=1,
                        default=[DEFAULT_THREADS],
                        help=("Specify the number of threads to use. 'C' is " +
                              "substitued for the number of cores. " +
                              "Default is %r. Examples: '1', '10' or '1.5C'.")
                        % DEFAULT_THREADS)
    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    threads = eval_thread_config(args.threads[0])
    indexer = ImageIndexer(repo, parallel_threads=threads)
    indexer.run()

if __name__ == '__main__':
    main()

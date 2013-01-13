#!/usr/bin/env python

import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))

import dfr.db
from dfr.bit_indexer import BitIndexer
from dfr.support import add_common_command_line_arguments, globs_to_regexp

DEFAULT_FILE_EXCLUDE = ".git,CVS,RCS"
DEFAULT_DIR_EXCLUDE = ""


def cleanup(patterns, default):
    assert patterns
    assert patterns[0] == default
    if len(patterns) == 1:
        return patterns
    del patterns[0]
    assert patterns
    result = []
    for i in patterns:
        assert len(i) == 1
        i = i[0]
        result += i.split(",")
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Index directories recursive.')
    parser.add_argument('roots', metavar='DIR', nargs='*', default=["."],
                        help="a directory to index " +
                        "(if not given '.' will be used)")
    add_common_command_line_arguments(parser)
    parser.add_argument('-x', '--exclude-files', metavar='GLOBPATTERNS',
                        nargs=1, action="append",
                        default=[DEFAULT_FILE_EXCLUDE],
                        help=("Exclude files based on comma separated " +
                              "glob patterns. Default is %r.") %
                        DEFAULT_FILE_EXCLUDE)
    parser.add_argument('-X', '--exclude-dirs', metavar='GLOBPATTERNS',
                        nargs=1, action="append",
                        default=[DEFAULT_DIR_EXCLUDE],
                        help=("Exclude directories based on comma separated " +
                              "glob patterns. Default is %r.") %
                        DEFAULT_DIR_EXCLUDE)

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    excluded_files = cleanup(args.exclude_files, DEFAULT_FILE_EXCLUDE)
    excluded_dirs = cleanup(args.exclude_dirs, DEFAULT_DIR_EXCLUDE)
    excluded_files = globs_to_regexp(excluded_files)
    excluded_dirs = globs_to_regexp(excluded_dirs)

    indexer = BitIndexer(repo, excluded_files, excluded_dirs)
    indexer.run(args.roots)

if __name__ == '__main__':
    main()

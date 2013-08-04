#!/usr/bin/env python

import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))

import dfr.db
from dfr.image_similar_finder import ImageSimilarFinder
from dfr.support import add_common_command_line_arguments


def report(sig, found, known):
    for i in found:
        assert i.content_id1 < i.content_id2

    for i in known:
        assert i.contentid1 < i.contentid2

    classified = []
    for i in found:
        got = None
        for j in known:
            if (i.content_id1, i.content_id2) == (j.contentid1, j.contentid2):
                got = j
                break
        if got:
            classified.append(got)

    known_not_found = []
    for i in known:
        got = None
        for j in found:
            if (i.contentid1, i.contentid2) == (j.content_id1, j.content_id2):
                got = j
                break
        if not got:
            known_not_found.append(i)

    t_p = len([x for x in classified if x.aresimilar == 1])
    f_p = len([x for x in classified if x.aresimilar == 0])
    f_n = len([x for x in known_not_found if x.aresimilar == 1])

    prec = float(t_p)/(t_p+f_p)
    rec = float(t_p)/(t_p+f_n)
    f_measure = 2*prec*rec/(prec+rec)

    print ("%10d | %12s | %10d | %12s | %10s | %10s | " +
           "%10s | %10.1f | %10.1f | %10.1f") % \
          (sig, "", len(found), len(classified), t_p, f_p, f_n,
           100 * prec, 100 * rec, 100 * f_measure)


def main():
    parser = argparse.ArgumentParser(
        description='Reports statistics about the different image signatures.')
    parser.add_argument('roots', metavar='DIR', nargs='*', default=["."],
                        help="a directory to scan for duplicate files " +
                        "(if not given '.' will be used)")
    add_common_command_line_arguments(parser)
    parser.add_argument('-s', '--min-similarity',
                        default=0.9,
                        help='require at least this image similarity')

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    known = repo.imagefeedback.find()
    positive = [x for x in known if x.aresimilar == 1]
    print ("There are %d classified image pairs. %d (%.1f%%) " +
           "are classifized as similar.") % \
          (len(known), len(positive), (100.0*len(positive))/len(known))
    print ("%10s | %12s | %10s | %12s | %10s | %10s | %10s " +
           "| %10s | %10s | %10s") % \
          ("Signature", "Description", "Detected", "Classified", "TP",
           "FP", "FN", "Precision", "Recall", "F-Measure")

    for sig, sim in [(1, 0.95), (2, 0.999), (3, 0.9),
                     (4, 0.95), (5, 0.8)]:
        finder = ImageSimilarFinder(repo, args.roots, sig, 0)
        pairs = list(finder.find(sim))
        report(sig, pairs, known)

if __name__ == '__main__':
    main()

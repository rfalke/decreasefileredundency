#!/bin/sh

set -e
#set -x

if true; then
    SIZE=20000
    PROF=""
else
    SIZE=2000
    PROF="valgrind --tool=callgrind  --dump-instr=yes --collect-jumps=yes"
fi

OUT=$(mktemp -d)
echo "$SIZE $SIZE 1 12 32 31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14 13 12 11 10 9 8 7 6 5 4 3 2 1" >$OUT/input
hexdump -n $((16*$SIZE)) -v -e '/1 "%02X"' -e '/16 "\n"' /dev/urandom >>$OUT/input

$PROF ./target/calc_histogram_distance -t -q $OUT/input $OUT/output

#cat $OUT/output

rm -rf $OUT

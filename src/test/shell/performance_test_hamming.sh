#!/bin/sh

set -e
#set -x

if true; then
    SIZE=50000
    PROF=""
else
    SIZE=5000
    PROF="valgrind --tool=callgrind  --dump-instr=yes --collect-jumps=yes"
fi

OUT=$(mktemp -d)
echo "$SIZE 10 $SIZE 17 16 15 14 13 12 11 10 9 8 7 6 5 4 3 2 1" >$OUT/input
hexdump -n $((8*$SIZE)) -v -e '/1 "%02X"' -e '/8 "\n"' /dev/urandom >>$OUT/input

$PROF ./target/calc_hamming_distance -t -q $OUT/input $OUT/output

#cat $OUT/output

rm -rf $OUT

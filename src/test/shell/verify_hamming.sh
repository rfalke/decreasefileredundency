#!/bin/sh

set -e
#set -x

OUT=$(mktemp -d)
target/calc_hamming_distance -q src/test/shell/hamming_input_data $OUT/output
diff -u src/test/shell/expected_output/hamming $OUT/output

rm -rf $OUT

#!/bin/sh

set -e
#set -x

OUT=$(mktemp -d)
target/calc_histogram_distance -q src/test/shell/histogram_input_data_gray $OUT/output
diff -u src/test/shell/expected_output/histogram_gray $OUT/output

target/calc_histogram_distance -q src/test/shell/histogram_input_data_rgb $OUT/output
diff -u src/test/shell/expected_output/histogram_rgb $OUT/output

rm -rf $OUT

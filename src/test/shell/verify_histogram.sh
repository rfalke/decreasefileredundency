#!/bin/sh

set -e
#set -x

OUT=$(mktemp -d)
target/calc_histogram_distance -q src/test/shell/histogram_input_data_gray $OUT/output
diff -u src/test/shell/histogram_expected_output_gray $OUT/output

target/calc_histogram_distance -q src/test/shell/histogram_input_data_rgb $OUT/output
diff -u src/test/shell/histogram_expected_output_rgb $OUT/output

rm -rf $OUT

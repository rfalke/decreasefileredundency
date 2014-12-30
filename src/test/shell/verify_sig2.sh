#!/bin/sh

set -e
#set -x

DIR=$(mktemp -d)

./src/main/perl/get_sig2.pl <src/test/shell/sig2_input >$DIR/actual_sig2_output
diff -u src/test/shell/expected_output/image_raw_sig2 $DIR/actual_sig2_output

rm -rf $DIR $DB

#!/bin/sh

set -e
#set -x

DIR=$(mktemp -d /tmp/tmp.XXXXXX)

if ./src/main/perl/get_sig2.pl <src/test/shell/sig2_input >$DIR/actual_sig2_output
then
    diff -u src/test/shell/expected_output/image_raw_sig2 $DIR/actual_sig2_output
else
    echo "Image magick perl bindings missing?!"
fi
rm -rf $DIR $DB

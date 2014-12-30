#!/bin/sh

set -e
#set -x

for sig in 1 2 3 4 5
do
    echo "##### testing with signature type $sig"
    TMPDIR=$(mktemp -d)
    DIR=$(pwd)/src/test/images
    DB=$(mktemp)
    OUT=$(mktemp)
    rm $DB

    python src/main/python/dfr/f_index.py --db-file=$DB $DIR
    python src/main/python/dfr/f_image.py --db-file=$DB -s 0.8 -S $sig -T 1

    # csv
    python src/main/python/dfr/f_finddupes.py --db-file=$DB -w image -s 1.0 -S $sig -t csv $DIR | sed "s|$DIR/||g" >$TMPDIR/actual_image_output
    diff -u src/test/shell/expected_output/image_sig${sig}_csv $TMPDIR/actual_image_output
    python src/main/python/dfr/f_finddupes.py --db-file=$DB -w image -s 1.0 -S $sig -t csv -o $OUT $DIR; sed <$OUT "s|$DIR/||g" >$TMPDIR/actual_image_output
    diff -u src/test/shell/expected_output/image_sig${sig}_csv $TMPDIR/actual_image_output

    # json
    python src/main/python/dfr/f_finddupes.py --db-file=$DB -w image -s 1.0 -S $sig -t json $DIR | sed "s|$DIR/||g" >$TMPDIR/actual_image_output
    diff -u src/test/shell/expected_output/image_sig${sig}_json $TMPDIR/actual_image_output
    python src/main/python/dfr/f_finddupes.py --db-file=$DB -w image -s 1.0 -S $sig -t json -o $OUT $DIR; sed <$OUT "s|$DIR/||g" >$TMPDIR/actual_image_output
    diff -u src/test/shell/expected_output/image_sig${sig}_json $TMPDIR/actual_image_output

    rm -rf $DB $TMPDIR $OUT
    echo "##### finished testing with signature type $sig"
done

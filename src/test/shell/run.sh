#!/bin/sh

set -e
#set -x

DIR=$(mktemp -d)
DB=$(mktemp)
rm $DB

dd if=/dev/urandom of=$DIR/base bs=1k count=42
cp $DIR/base $DIR/base2
cp $DIR/base $DIR/larger
echo >>$DIR/larger

python src/main/python/dfr/f_index.py --db-file=$DB $DIR

python src/main/python/dfr/f_finddupes.py --db-file=$DB -c $DIR | sed "s|$DIR/||g" >$DIR/actual_bit_equal_output
diff -u $DIR/actual_bit_equal_output src/test/shell/expected_bit_equal_output

python src/main/python/dfr/f_finddupes.py --db-file=$DB -c -t $DIR | sed "s|$DIR/||g" >$DIR/actual_bit_truncated_output
diff -u $DIR/actual_bit_truncated_output src/test/shell/expected_bit_truncated_output

rm -rf $DIR $DB
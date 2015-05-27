#!/bin/sh

set -e
#set -x

DIR=$(mktemp -d /tmp/tmp.XXXXXX)
DIR=$(cd $DIR;pwd -P)
DB=$(mktemp /tmp/tmp.XXXXXX)
OUT=$(mktemp /tmp/tmp.XXXXXX)
rm $DB

dd if=/dev/urandom of=$DIR/base bs=1k count=42
cp $DIR/base $DIR/base2
cp $DIR/base $DIR/larger
cp $DIR/base $DIR/ignore
mkdir $DIR/ignore_dir
cp $DIR/base $DIR/ignore_dir/base2
echo >>$DIR/larger

dd if=/dev/urandom of=$DIR/another_base bs=1k count=100
cp $DIR/another_base $DIR/another_base2
cp $DIR/another_base $DIR/another_base3

python src/main/python/dfr/f_index.py --db-file=$DB -x '*gn*re' -X 'ig[a-n]*_dir' $DIR

# bitequal, csv
python src/main/python/dfr/f_finddupes.py --db-file=$DB -t csv $DIR | sed "s|$DIR/||g" >$DIR/actual_bit_equal_output
diff -u src/test/shell/expected_output/bit_equal_csv $DIR/actual_bit_equal_output
python src/main/python/dfr/f_finddupes.py --db-file=$DB -t csv -o $OUT $DIR; sed <$OUT "s|$DIR/||g" >$DIR/actual_bit_equal_output
diff -u src/test/shell/expected_output/bit_equal_csv $DIR/actual_bit_equal_output

# bitequal, json
python src/main/python/dfr/f_finddupes.py --db-file=$DB -t json $DIR | sed "s|$DIR/||g" >$DIR/actual_bit_equal_output
diff -u src/test/shell/expected_output/bit_equal_json $DIR/actual_bit_equal_output
python src/main/python/dfr/f_finddupes.py --db-file=$DB -t json -o $OUT $DIR; sed <$OUT "s|$DIR/||g" >$DIR/actual_bit_equal_output
diff -u src/test/shell/expected_output/bit_equal_json $DIR/actual_bit_equal_output

# truncated, csv
python src/main/python/dfr/f_finddupes.py --db-file=$DB -t csv -w truncated $DIR | sed "s|$DIR/||g" >$DIR/actual_bit_truncated_output
diff -u src/test/shell/expected_output/bit_truncated_csv $DIR/actual_bit_truncated_output
python src/main/python/dfr/f_finddupes.py --db-file=$DB -t csv -w truncated -o $OUT $DIR; sed <$OUT "s|$DIR/||g" >$DIR/actual_bit_truncated_output
diff -u src/test/shell/expected_output/bit_truncated_csv $DIR/actual_bit_truncated_output

rm -rf $DIR $DB $OUT

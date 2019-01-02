#!/bin/bash
#
# Split input into 10 shards, shuffle them, and concatenate the results.  This
# takes 10 times less RAM than running `shuf` directly, and the results can be
# concatenated together for a shuffle that's not entirely random but close
# enough for machine learning.
#
# Argument 1: filename for final output
# Argument 2: Unique identifier to distinguish this shuffle task from others
# Input comes from standard in
set -e
mkdir -p data/tmp
split -n r/10 -a 1 -d - "data/tmp/split.${2}."
for num in `seq 0 9`; do
    shuf "data/tmp/split.${2}.$num" > "data/tmp/shuf.${2}.$num"
    rm "data/tmp/split.${2}.$num"
done
cat data/tmp/shuf.${2}.* | gzip -c > $1
rm data/tmp/shuf.${2}.*

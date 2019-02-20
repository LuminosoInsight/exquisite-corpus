# Read (from stdin) the result of encoding a text file with a trained
# SentencePiece model (as id's).  Write all lines containing  fewer than
# (the input variable) MAX_LENGTH ids into separate output files, one for
# each length up to MAX_LENGTH, named FILE_PREFIX0.txt, ..., FILE_PREFIXk.txt
# (where k is the value of MAX_LENGTH) except that no empty files will be
# written.  Input lines containing more than MAX_LENGTH ids will be split
# into non-overlapping chunks with sizes between (the input variables)
# MIN_CHUNK and MAX_CHUNK (inclusive), with any ids remaining at the end of
# the line discarded; if MAX_CHUNK >= 2 * MIN_CHUNK - 1 no ids will be
# discarded.  Note that the input variables should satisfy the constraints
# 1 <= MIN_CHUNK <= MAX_CHUNK <= MAX_LENGTH.
#
# Example invocation:
#   cat input.txt | awk -f split_sentencepiece_ids.awk \
#     -v MAX_LENGTH=70 -v MIN_CHUNK=35 -v MAX_CHUNK=70 \
#     -v FILE_PREFIX=data/sentencepiece/en.spm_encoded_ids_

BEGIN {
    if (MIN_CHUNK < 1) {
        print ("Error: MIN_CHUNK (" MIN_CHUNK ") < 1.") > "/dev/stderr"
        exit 1
    }
    if (MAX_CHUNK < MIN_CHUNK) {
        print ("Error: MAX_CHUNK (" MAX_CHUNK ") < MIN_CHUNK (" MIN_CHUNK ").") > "/dev/stderr"
        exit 1
    }
    if (MAX_LENGTH < MAX_CHUNK) {
        print ("Error: MAX_LENGTH (" MAX_LENGTH ") < MAX_CHUNK (" MAX_CHUNK ").") > "/dev/stderr"
        exit 1
    }
}

{
    if (NF <= MAX_LENGTH) {
        filename = FILE_PREFIX NF ".txt"
        print $0 > filename
    } else {  # break long inputs into shorter chunks
        # First we write one fewer than the maximum possible number of chunks
        # of size MIN_CHUNK.  The remaining ids form a chunk of size
        # MIN_CHUNK + r, where r is the remainder on dividing the number
        # of ids by MIN_CHUNK.  If MIN_CHUNK + r <= MAX_CHUNK we can write
        # one final chunk of this size; otherwise we can write one more
        # chunk of size MAX_CHUNK and discard the remaining ids.  Note that
        # we will never discard any ids if MAX_CHUNK >= 2 * MIN_CHUNK - 1
        # (since r < MIN_CHUNK).
        n_ids = split($0, ids)
        quotient = int(n_ids / MIN_CHUNK)  # > 0 as MIN_CHUNK <= MAX_LENGTH
        remainder = n_ids - MIN_CHUNK * quotient
        n_remaining = MIN_CHUNK + remainder
        if (n_remaining <= MAX_CHUNK) {
            length_of_last_chunk = n_remaining
        } else {
            length_of_last_chunk = MAX_CHUNK
        }
        i_start = 1  # awk indexing is 1-based
        start_of_last_chunk = 1 + MIN_CHUNK * (quotient - 1)
        end_of_last_chunk = start_of_last_chunk + length_of_last_chunk - 1
        filename = FILE_PREFIX MIN_CHUNK ".txt"
        while (i_start < start_of_last_chunk) {
            i_end = i_start + MIN_CHUNK - 1
            chunk = ids[i_start++]
            while (i_start <= i_end) {
                chunk = chunk " " ids[i_start++]
            }
            print chunk > filename
        }
        # At this point i_start == start_of_last_chunk.
        chunk = ids[i_start++]
        while (i_start <= end_of_last_chunk) {
            chunk = chunk " " ids[i_start++]
        }
        filename = FILE_PREFIX length_of_last_chunk ".txt"
        print chunk > filename
    }
}

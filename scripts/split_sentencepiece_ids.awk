# Read (from stdin) the result of encoding a text file with a trained
# SentencePiece model (as id's).  Write all lines containing  fewer than
# (the input variable) MAX_LENGTH ids into separate output files, one for
# each length up to MAX_LENGTH, named FILE_PREFIX0.txt, ..., FILE_PREFIXk.txt
# (where k is the value of MAX_LENGTH) except that no empty files will be
# written.  Input lines containing more than MAX_LENGTH ids will be split
# into non-overlapping chunks with sizes chosen uniformly at random between
# (the input variables) MIN_CHUNK and MAX_CHUNK (inclusive), with any ids
# remaining at the end of the line discarded.  Note that the input variables
# should satisfy the constraints 1 <= MIN_CHUNK <= MAX_CHUNK <= MAX_LENGTH.
#
# Example invocation:
#   cat input.txt | awk -f split_sentencepiece_ids.awk \
#     -v MAX_LENGTH=300 -v MIN_CHUNK=15 -v MAX_CHUNK=30 \
#     -v FILE_PREFIX=data/sentencepiece/en.spm_encoded_ids_

# Return a random integer in [m, n].
function randint(m, n) {
    return m + int((n + 1 - m) * rand())
}

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
        n_ids = split($0, ids)
        i_start = 1  # awk indexing is 1-based
        while (i_start <= n_ids) {
            i_end = i_start + randint(MIN_CHUNK, MAX_CHUNK) - 1
            if (i_end > n_ids) {
                i_end = n_ids
            }
            len = i_end - i_start + 1
            if (len < MIN_CHUNK) {  # don't write any final, runt, chunk
                break
            }
            chunk = ids[i_start++]
            while (i_start <= i_end) {
                chunk = chunk " " ids[i_start++]
            }
            filename = FILE_PREFIX len ".txt"
            print chunk > filename
        }
    }
}

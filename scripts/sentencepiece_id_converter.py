#!/usr/bin/env python
"""
Utility script to read a text file containing space-delimited sequences of
SentencePiece encoding ids (integers), and convert it to an .npy file.
The input must have the same number of ids on every line, and the output
will store a 2D array with that many columns (and one row for each line of
the input).  The input file (base) name (minus any extension) must have the
form 'length_n' where n is number of ids per line.
"""

import numpy as np
import os
import re
import sys


def main(input, output):
    # First parse the input file name to find the width of the data.
    basename = os.path.splitext(os.path.basename(input))[0]
    match = re.match(r"length_(\d+)$", basename)
    if match is None:
        raise ValueError("Invalid file name {}.".format(input))
    else:
        numeral = match.group(1)
        try:
            n_fields = int(numeral)
        except ValueError:
            raise ValueError(
                "Invalid numeral {} in file name {}.".format(numeral, input)
            )

    # Now read the input file to establish its length and check the width.
    n_lines = 0
    with open(input, "rt", encoding="utf-8") as fp:
        for line in fp:
            n_lines += 1
            if n_fields != len(line.split()):
                raise ValueError(
                    "Input file {} has invalid width at line {}.".format(input, n_lines)
                )

    # Allocate a result array.
    result = np.empty((n_lines, n_fields), dtype=np.int64)

    # Re-read the input, and populate the result.
    with open(input, "rt", encoding="utf-8") as fp:
        for i_line, line in enumerate(fp):
            result[i_line] = np.array([int(i) for i in line.split()])

    # Write the output.
    np.save(file=output, arr=result)


if __name__ == "__main__":
    main(input=sys.argv[1], output=sys.argv[2])

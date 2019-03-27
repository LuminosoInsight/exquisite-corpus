"""
Utility to read space-delimited tokens on lines from stdin, and distribute
the lines to a fixed number of output files based on length (number of tokens),
splitting up any input lines longer than the fixed maximum length.
"""

import click
import numpy as np
import sys


class Writer:
    """
    Context manager handling opening, closing, and writing to a fixed-size
    set of output files.
    """

    def __init__(self, file_prefix, max_length):
        self.out_files = []
        for length in range(max_length + 1):
            path = "{}{}.txt".format(file_prefix, length)
            out_file = open(path, "wt", encoding="utf-8")
            self.out_files.append(out_file)

    def write(self, chunk):
        self.out_files[len(chunk)].write(" ".join(chunk) + "\n")

    def close(self):
        for out_file in self.out_files:
            out_file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class ChunkMaker:
    """
    Provides a method for generating bounded-size chunks of long input lists.
    """

    def __init__(self, min_chunk_length, max_chunk_length, seed=101):
        self.min_chunk_length = min_chunk_length
        self.max_chunk_length = max_chunk_length
        self.rng = np.random.RandomState(seed=seed)
        self.length_bound = np.max(
            [2 * self.min_chunk_length, self.max_chunk_length + 1]
        )

    def make_chunks(self, original_chunk):
        # Split big chunks into smaller ones, yielding chunks that satisfy the
        # minimum and maximum size constraints, until there is nothing left to
        # split.  Chunks shorter than twice the minimum chunk size must not be
        # split; if they are longer than the maximum size (which won't happen
        # if the maximum size is at least twice the minimum, minus one), we
        # must discard part of the chunk (we choose to discard the tail).  Other
        # chunks no longer than the maximum size will not be split (so we favor
        # long chunks).  The remaining chunks are split into two pieces each
        # at least of the minimum size.
        chunks = [original_chunk]
        while len(chunks) > 0:
            chunk = chunks.pop()
            length = len(chunk)
            if length < self.length_bound:
                yield chunk[: self.max_chunk_length]
            else:
                split = self.rng.randint(
                    self.min_chunk_length, length - self.min_chunk_length + 1
                )
                chunks.append(chunk[:split])
                chunks.append(chunk[split:])


@click.command()
@click.option(
    "--file-prefix",
    help=(
        "Prefix for output file paths.  E.g. if this argument is 'foo' "
        "then output files foo0.txt, foo1.txt, ... will be written."
    ),
)
@click.option(
    "--max-length",
    type=click.INT,
    help="Maximum output length.  Inputs longer than this will be split into pieces.",
)
@click.option(
    "--min-chunk-length",
    type=click.INT,
    help="Minimum size of pieces into which to split long input lines.",
)
@click.option(
    "--max-chunk-length",
    type=click.INT,
    help="Maximum size of pieces into which to split long input lines.",
)
@click.option(
    "--random-seed",
    type=click.INT,
    default=101,
    help="Seed for random generator (used to pick piece sizes).",
)
def slice_sentencepiece_ids(
    file_prefix, max_length, min_chunk_length, max_chunk_length, random_seed=101
):
    """
    Read space-delimited text lines from stdin and write the lines
    to output files corresponding to the length (number of space-
    delimited tokens) of each line.  Long lines will be split into
    pieces before being written.
    """
    assert 1 <= min_chunk_length <= max_chunk_length <= max_length
    chunker = ChunkMaker(min_chunk_length, max_chunk_length, seed=random_seed)
    with Writer(file_prefix, max_length) as writer:
        for line in map(str.rstrip, sys.stdin):
            tokens = line.split()
            if len(tokens) <= max_length:
                writer.write(tokens)
            else:
                for chunk in chunker.make_chunks(tokens):
                    writer.write(chunk)


if __name__ == "__main__":
    slice_sentencepiece_ids()

import click
import hashlib
import sys


class SpmFileSplitter:
    """
    Does the work of assigning input lines at random to one of two
    destinations, ensuring that multiple occurances of the same input
    line (after normalizing away any whitespace differences) go to the
    same destination.
    """

    def __init__(self, fraction, seed, digest_size=8):
        self.digest_size = digest_size  # bytes (so x8 for bits)
        self.threshold = int(0.5 + fraction * pow(2, 8 * self.digest_size))
        self.seed = str(seed).encode("utf-8")

    def __call__(self, line):
        normalized_line = " ".join(line.lstrip().rstrip().split())
        seeded_encoded_line = self.seed + normalized_line.encode("utf-8")
        hash = int(
            hashlib.blake2b(
                seeded_encoded_line, digest_size=self.digest_size
            ).hexdigest(),
            base=16,
        )
        destination = 0 if hash < self.threshold else 1
        return destination


@click.command()
@click.option(
    "--output-file1",
    type=click.Path(dir_okay=False, path_type=str),
    help="Path to file into which the first split of the input is written.",
)
@click.option(
    "--fraction1",
    type=click.FLOAT,
    help="Fraction of input to split into the first output file.",
)
@click.option(
    "--output-file2",
    type=click.Path(dir_okay=False, path_type=str),
    help="Path to file into which the second split of the input is written.",
)
@click.option(
    "--fraction2",
    type=click.FLOAT,
    help="Fraction of input to split into the second output file.",
)
@click.option(
    "--output-file3",
    type=click.Path(dir_okay=False, path_type=str),
    help="Path to file into which the third (remaining) split of the input is written.",
)
@click.option(
    "--seed",
    type=click.INT,
    default=101,
    help=("Seed for randomizing selection of splits (defaults to 101)."),
)
def split_sentencepiece_ids(
    output_file1, fraction1, output_file2, fraction2, output_file3, seed
):
    """
    Split stdin into thtree disjoint pieces line by line, the two pieces of
    sizes (approximately) the given fractions of the size of stdin.  Care is
    taken that even if a line appears twice (perhaps with different
    whitespace) all occurances will go the same piece.  The pieces are written
    to the output paths given.
    """
    assert 0 <= fraction1 <= 1
    assert 0 <= fraction2 <= 1
    assert fraction1 + fraction2 <= 1
    fraction1and2 = fraction1 + fraction2
    if fraction1and2 == 0:
        fraction1from1and2 = 0
    else:
        fraction1from1and2 = fraction1 / fraction1and2
    splitter1and2 = SpmFileSplitter(fraction=fraction1and2, seed=seed)
    splitter1from2 = SpmFileSplitter(fraction=fraction1from1and2, seed=seed + 1)

    with open(output_file1, "wt", encoding="utf-8") as fp1:
        with open(output_file2, "wt", encoding="utf-8") as fp2:
            with open(output_file3, "wt", encoding="utf-8") as fp3:
                for line in sys.stdin:
                    if splitter1and2(line) != 0:
                        fp3.write(line)
                    elif splitter1from2(line) == 0:
                        fp1.write(line)
                    else:
                        fp2.write(line)


if __name__ == "__main__":
    split_sentencepiece_ids()

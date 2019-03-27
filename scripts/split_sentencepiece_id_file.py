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
    "--output-file",
    type=click.Path(dir_okay=False, path_type=str),
    help="Path to file into which the first split of the input is written.",
)
@click.option(
    "--fraction",
    type=click.FLOAT,
    help="Fraction of input to split into the named output file.",
)
@click.option(
    "--seed",
    type=click.INT,
    help=(
        "Seed for randomizing selection of splits; if you use this script "
        "twice (to re-split the output of a prior invocation) you must "
        "supply distinct seeds to the two invocations."
    ),
)
def split_sentencepiece_ids(output_file, fraction, seed):
    """
    Split stdin into two disjoint pieces line by line, the first piece of
    size (approximately) the given fraction of the size of stdin.  Care is
    taken that even if a line appears twice (perhaps with different
    whitespace) all occurances will go to one or the other piece rather
    than some going to the first piece and some to the second.  The first
    piece is written to the output path given, the second to stdout.
    """
    splitter = SpmFileSplitter(fraction=fraction, seed=seed)
    with open(output_file, "wt", encoding="utf-8") as fp:
        destinations = [fp, sys.stdout]
        for line in sys.stdin:
            destination = destinations[splitter(line)]
            destination.write(line)


if __name__ == "__main__":
    split_sentencepiece_ids()

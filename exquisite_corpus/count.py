from collections import Counter
from ftfy.fixes import uncurl_quotes
from wordfreq.tokens import tokenize
import regex

PUNCT_RE = regex.compile(r'\p{punct}')


def count_tokenized(infile, outfile):
    """
    Take in a file that's been tokenized (such as with 'xc tokenize'), count
    its tokens, and write the ones with a count of at least 2.
    """
    counts = Counter()
    total = 0
    for line in infile:
        line = uncurl_quotes(line.rstrip())
        if line:
            toks = [t.strip("'") for t in line.split(' ')]
            counts.update(toks)
            total += len(toks)

    # adjusted_counts drops the items that only occurred once
    one_each = Counter(counts.keys())
    adjusted_counts = counts - one_each

    # Write the counted tokens to outfile
    print('__total__\t{}'.format(total), file=outfile)
    for token, adjcount in adjusted_counts.most_common():
        if not PUNCT_RE.match(token):
            print('{}\t{}'.format(token, adjcount + 1), file=outfile)


def recount_messy(infile, outfile, language):
    """
    Take in a file of counts from another source (such as Google Books), and
    make it consistent with our tokenization and format.
    """
    counts = Counter()
    total = 0
    for line in infile:
        line = line.rstrip()
        if line and not line.startswith('__total__'):
            text, strcount = line.split('\t', 1)
            count = int(strcount)
            for token in tokenize(text, language):
                counts[token] += count
                total += count

    # Write the counted tokens to outfile
    print('__total__\t{}'.format(total), file=outfile)
    for token, count in counts.most_common():
        if not PUNCT_RE.match(token):
            print('{}\t{}'.format(token, count), file=outfile)


def counts_to_freqs(infile, outfile):
    total = None
    for line in infile:
        word, strcount = line.rstrip().split('\t', 1)
        count = int(strcount)
        if word == '__total__':
            total = count
        else:
            freq = count / total
            print('{:.5g}\t{}'.format(freq, count), file=outfile)

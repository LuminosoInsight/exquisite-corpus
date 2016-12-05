from wordfreq import tokenize


def tokenize_file(infile, outfile, language):
    """
    Take in a file of plain text, tokenize it as the given language, and write
    the result as lines of space-separated tokens.
    """
    for line in infile:
        tokens = tokenize(line.rstrip(), language, include_punctuation=True, external_wordlist=True)
        print(' '.join(tokens), file=outfile)


def scan_xml2(infile, outfile):
    """
    Takes in a file in the 'xml2' intermediate format -- the line-based
    output of the 'xml2' command-line tool, where each line contains the
    XPath and text value of each node it encounters.

    Given such a file containing texts enclosed by <s> tags, with individual
    tokens enclosed by <w> tags, output lines of space-separated tokens
    where each <s> is a separate line.
    """
    tokens = []
    for line in infile:
        line = line.rstrip()
        if line == '/document/s':
            print(' '.join(tokens), file=outfile)
            tokens.clear()
        elif line.startswith('/document/s/w='):
            xpath, token = line.rstrip().split('=', 1)
            tokens.append(token.casefold())


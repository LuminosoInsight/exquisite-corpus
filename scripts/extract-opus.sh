#!/bin/sh

# This script takes in a gzipped OPUS XML file, in the format that comes from
# http://opus.lingfil.uu.se/OpenSubtitles2016.php, on standard input. This file
# contains tokens inside <w> tags. We want to get just these tokens, one per
# line, with blank lines between subtitles. This can be done quickly by piping
# together a few commands:
#
# - zcat uncompresses gzip data on standard in to standard out.
#
# - xml2 transforms XML into a line-based format, where text nodes have the
#   format XPATH=TEXT, as in:
#
#       /document/s/w=的
#
#   and nodes that have just been completed are simply represented by their
#   XPath:
#
#       /document/s
#
# - xc scan_xml2 uses the command-line entry point to Exquisite Corpus (xc)
#   to read this format and output lines of space-separated tokens.

zcat | xml2 | xc scan_xml2


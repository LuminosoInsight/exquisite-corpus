#!/bin/sh

# This script takes in a gzipped OPUS XML file, in the format that comes from
# http://opus.lingfil.uu.se/OpenSubtitles2016.php, on standard input. This file
# contains tokens inside <w> tags. We want to get just these tokens, one per
# line, with blank lines between subtitles. This can be done quickly by piping
# together a few command-line tools:
#
# zcat uncompresses gzip data on standard in to standard out.
#
# xml2 transforms XML into a line-based format, where text nodes have the
# format XPATH=TEXT, as in:
#
#     /document/s/w=的
#
# Other nodes are introduced by just their xpath. For example, <w> nodes are
# grouped into <s> nodes, representing entire subtitles. Each new <s> node
# outputs the line:
#
#     /document/s
#
# So we can get the blank lines between subtitles by also grepping for that
# exact line and outputting a blank line.
#
# We'll provide two commands to sed, both of the form s/PATTERN/REPLACEMENT/p .
# This command matches the regular expression PATTERN, replaces it with
# REPLACEMENT (where references like \1 can refer to backslashed parenthesized
# groups that matched), and only outputs the line if it made such a replacement.
# So the expression to match lines containing 'w=' and output what came after
# 'w=' is:
#
#   s/^.*w=\(.*\)$/\1/p
#
# And the command to output a blank line for each /document/s is:
#
#   s/^\/document\/s$//p

zcat | xml2 | sed -n -e 's/^.*w=\(.*\)$/\1/p' -e 's/^\/document\/s$//p'


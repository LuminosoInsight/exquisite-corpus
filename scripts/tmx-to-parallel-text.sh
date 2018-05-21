#!/bin/bash
#
# Standard input is a translation file in TMX (XML) format. Standard out is a
# four-column tab-separated text file, containing these columns:
#
# 1. lang1, a language tag
# 2. A sentence in lang1
# 3. lang2, another language tag
# 4. The correspnoding sentence in lang2
#
# Columns 1 and 3 are a sanity-check, as they will contain the same value on
# every line.
#
# This script depends on xml2 (a command-line XML processor) and an Awk script
# alongside it.

source_dir=$(dirname $BASH_SOURCE)
xml2 | awk -f $source_dir/tmx-language-tagger.awk | paste - -

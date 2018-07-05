# Take in TMX data that's been run through xml2 (a command-line streaming XML
# processor), and output parallel text. The lines occur in pairs, and each line
# contains its language tag, a tab, and the text.
#
# The pairs of corresponding lines (in different languages) can be combined
# onto the same line by piping the result to the shell command 'paste - -'.

# Output from this script will be tab-separated
BEGIN {
    OFS="\t"
    valid = 1
}

# If we see "prop=0.0", that's a value from either Zipporah or Bicleaner
# telling us that this entry is garbage.
/prop=0\.0$/ {
    valid = 0
}

# At the end of each text unit, reset our assumption that the next example
# will be valid, until we're told otherwise.
/\/tu$/ {
    valid = 1
}

# The idiom that follows allows matching something on one line, and processing
# both that line and the following line.
#
# This was my starting point:
# https://stackoverflow.com/questions/14350856/can-awk-patterns-match-multiple-lines

# Match a <tuv> node with an "@xml:lang" attribute, as output by the xml2 tool
/tuv\/@xml:lang=/ {
    if (valid == 1) {
        # Extract the language tag, by splitting on "@xml:lang=" and storing the part afterward
        split($0, langParts, "@xml:lang=")
        lang = langParts[2]

        # Go to the next line
        getline

        # Extract the value of the "seg" attribute, which is the text
        split($0, textParts, "tu/tuv/seg=")
        text = textParts[2]

        print lang, text
    }
}


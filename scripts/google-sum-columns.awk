# make sure to output tab-separated data
BEGIN {
    OFS="\t"
}

{
    total = 0;

    # Terms have an optional part-of-speech tag, attached with an underscore.
    # Split on underscores so that the untagged term is term[1].
    split($1, term, "_");

    # Iterate through the rest of the columns, which contain values like
    # '1999,3,2', containing a year, the number of matches in that year, and
    # the number of distinct books that match that term in that year. We want
    # the middle value, and we add it to the running total.
    for (i=2; i <= NF; i++) {
        split($i, yearentry, ",");
        total += yearentry[2];
    }

    # Output the untagged term and the total occurrences.
    print term[1], total
}

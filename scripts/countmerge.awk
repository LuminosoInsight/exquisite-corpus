# Given a tab-separated, sorted file where each line is a key and a count,
# merge adjacent lines with the same key by adding their counts.

BEGIN {
    # Input and output are separated by tabs only
    FS = "\t"
    OFS = "\t"

    # Initialize the current count.
    # We use the empty string as a sentinel value, indicating that we haven't
    # seen a key yet. We won't output a total for the empty string.
    key = ""
    count = 0
}

# This block has no condition, so it runs on every line.
{
    if ($1 == key) {
        # The key matches the current key, so add to the count.
        count += $2
    } else {
        # This is a new key. First, output the old key and its count.
        if (key != "") {
            print key, count
        }
        # Now set the key to the new key, with the count we've just seen.
        # Concatenate the key with the empty string to force it to have string
        # type; otherwise, for example, "0" and "00" would be considered the
        # same key.
        key = $1""
        count = $2
    }
}

END {
    # Output the final key and its count.
    print key, count
}

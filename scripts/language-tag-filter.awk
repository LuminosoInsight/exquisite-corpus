# Select lines in the appropriate language, either because they have a tab-
# separated language tag, or because there is no language tag and they are
# assumed to be in the appropriate language.

BEGIN {
    # Input is tab-separated
    FS = "\t"

    # Get the language passed in with, for example, "-v lang=en"
    lang = lang
}

# This block has no condition, so it runs on every line.
{
    if ($1 == lang) {
        print $2
    } else if ($2 == "" && length($1)) {
        print $1
    }
}

"""
We would like to ignore a list of subreddits that would be sources of very bad
data. So that we don't have to do extensive, subjective research to make the
decision of which subreddits are bad, we exclude only the very worst:
subreddits that have been banned by the Reddit admins. Comments from these
subreddits that appear in the archive (from before they were banned) are
probably bad data.

This list _itself_ is bad. The list of banned subreddit names contains a high
density of hateful ideas, including racial slurs. We don't want to enshrine
this list in our code.

Therefore, what we commit to the code is the list of mmh3 hashes of the
subreddit names. The input is the text from
https://www.reddit.com/r/ListOfSubreddits/wiki/banned (which Reddit
unfortunately does not allow scripts to access), and the output is a list of
hashes suitable for pasting into reddit_ban_data.py.
"""

import mmh3


bad_hashes = set()
for line in open('extra/reddit-ban-list.txt'):
    if line.startswith('/r/'):
        name = line.strip()[3:].casefold()
        name_hash = mmh3.hash(name)
        bad_hashes.add(name_hash)

if __name__ == '__main__':
    for ahash in sorted(bad_hashes):
        print(f'    {ahash},')

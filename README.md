Exquisite Corpus makes use of various libraries and command-line tools to
process data correctly efficiently. As something that is run on a development
machine, it uses the best, fastest libraries it can, though this leads to
somewhat complex system requirements.

You will need three programming environments installed:

- Python 3.4 or later
- Haskell, installed with `haskell-stack`, used to compile and run `wikiparsec`
- The Rust programming language, version 1.14 or later, installed with `rustup`,
  used to compile `countmerge`

You also need certain tools to be available:

- The `mecab-dev` C library (apt install mecab-dev)
- The ICU Unicode libraries (apt install libicu-dev)
- The JSON processor `jq` (apt install jq)
- countmerge (https://github.com/rspeer/countmerge)
- wikiparsec (https://github.com/LuminosoInsight/wikiparsec)


## Installation

Some steps here probably need to be filled in better.

- Install system-level dependencies:

```sh
apt install python3-dev haskell-stack mecab-dev libicu-dev jq
```

- Install Rust: https://www.rust-lang.org/en-US/install.html

- Clone, build, and install `wikiparsec`:

```sh
git clone https://github.com/LuminosoInsight/wikiparsec
cd wikiparsec
stack install
```

- Install `countmerge`:

```sh
cargo install countmerge
```

- Finally, return to this directory and install `exquisite-corpus` itself,
  along with the Python dependencies it manages:

```sh
python setup.py develop
```

## Getting data

Most of the data in Exquisite Corpus will be downloaded from places where it
can be found on the Web. However, some inputs must be obtained separately.

A corpus of Reddit comments from 2007-2015 can be obtained over BitTorrent [1]:

[1]: https://www.reddit.com/r/datasets/comments/3bxlg7/i_have_every_publicly_available_reddit_comment/

Extract it into `data/raw/reddit`, so that there are directories named `data/raw/reddit/2007` and so on.

Twitter data cannot be distributed due to the Twitter API's terms of use. If
you have a collection of tweets, put their text in `data/raw/twitter-2015.txt`,
one tweet per line. Or just put an empty file there.


## Building

Make sure you have lots of disk space available in the `data` directory, which
may have to be a symbolic link to an external hard disk.

Run:

```sh
snakemake -j 8
```

...and wait a day or two for results, or a crash that may tell you what you need to fix.

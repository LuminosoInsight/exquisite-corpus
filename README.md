This code represents the build process for [wordfreq][], among other things.
I've made it public because it's good to know where the data in wordfreq comes
from. However, I make no promises that you'll be able to run it if you don't
work at Luminoso.

[wordfreq]: https://github.com/LuminosoInsight/wordfreq

## Dependencies

Exquisite Corpus makes use of various libraries and command-line tools to
process data correctly and efficiently. As something that is run on a
development machine, it uses the best, fastest libraries it can, though this
leads to somewhat complex system requirements.

You will need these programming environments installed:

- Python 3.4 or later
- Haskell, installed with `haskell-stack`, used to compile and run `wikiparsec`

You also need certain tools to be available:

- The C library for `mecab` (apt install libmecab-dev)
- The ICU Unicode libraries (apt install libicu-dev)
- The JSON processor `jq` (apt install jq)
- The XML processor `xml2` (apt install xml2)
- The HTTP downloader `curl` (apt install curl)
- wikiparsec (https://github.com/LuminosoInsight/wikiparsec)


## Installation

Some steps here probably need to be filled in better.

- Install system-level dependencies:

```sh
apt install python3-dev haskell-stack libmecab-dev libicu-dev jq xml2 curl
```

- Clone, build, and install `wikiparsec`:

```sh
git clone https://github.com/LuminosoInsight/wikiparsec
cd wikiparsec
stack install
```

- If building _alignment_ files to get alignments for parallel corpus:
    - Compile `fast_align` by following the instructions at 
    https://github.com/clab/fast_align
    - Create a symbolic link to executable `fast_align` inside this directory 
    (executable `fast_align` is found in the directory where `fast_align` was compiled)

- Finally, return to this directory and install `exquisite-corpus` itself,
  along with the Python dependencies it manages:

```sh
pip install -e .
```

## Getting data

Most of the data in Exquisite Corpus will be downloaded from places where it
can be found on the Web. However, one input must be downloaded separately:
Twitter data cannot be distributed due to the Twitter API's terms of use.

If you have a collection of tweets, put their text in
`data/raw/twitter-2015.txt`, one tweet per line. Or just put an empty file
there.


## Building

Make sure you have lots of disk space available in the `data` directory, which
may have to be a symbolic link to an external hard disk.

Run:

```sh
snakemake -j 8
```

...and wait a day or two for results, or a crash that may tell you what you need to fix.

To build _parallel_ corpus, run `./build.sh parallel`. If you want _alignment_ files for
already built parallel corpus or want to build parallel corpus and alignment together, run
`./build.sh alignment`.
#!/usr/bin/env python3
# The above line is a lie, but it's close enough to the truth to make syntax
# highlighting happen. Snakemake syntax is an extension of Python 3 syntax.

SUPPORTED_LANGUAGES = {
    # OPUS's data files of OpenSubtitles 2016
    #
    # Include languages with at least 500 subtitle files, but skip:
    # - 'ze' because that's not a real language code
    #   (it seems to represent code-switching Chinese and English)
    # - 'th' because they don't really tokenize Thai, unsurprisingly,
    #   even when they claim to
    'opensubtitles': [
        'ar', 'bg', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'fa', 'fi',
        'fr', 'he', 'hr', 'hu', 'id', 'is', 'it', 'ja', 'ko', 'lt', 'mk', 'ms',
        'nl', 'no', 'pl', 'pt-PT', 'pt-BR', 'ro', 'ru', 'si', 'sk', 'sl', 'sq',
        'sr', 'sv', 'tr', 'uk', 'vi', 'zh-Hans', 'zh-Hant'
    ],

    # Europarl v7, which also comes from OPUS
    'europarl': [
        'bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr', 'hu', 'it',
        'lt', 'lv', 'nl', 'pl', 'pt-PT', 'ro', 'sk', 'sl', 'sv'
    ],

    # Sufficiently large, non-spammy Wikipedias.
    # See https://meta.wikimedia.org/wiki/List_of_Wikipedias -- we're looking
    # for Wikipedias that have at least 100,000 articles and a "depth" measure
    # of 10 or more (indicated that they're not mostly written by bots).
    'wikipedia': [
        'ar', 'bg', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'en', 'eo', 'es', 'et',
        'eu', 'fa', 'fi', 'fr', 'gl', 'he', 'hi', 'hu', 'hr', 'hy', 'id', 'it',
        'ja', 'ko', 'la', 'lt', 'lv', 'ms', 'nn', 'nb', 'nl', 'pl', 'pt',
        'ro', 'ru', 'sh', 'sk', 'sl', 'sr', 'sv', 'tr', 'uk', 'uz', 'vi', 'zh'
    ],

    # 99.2% of Reddit is in English. Some text that's in other languages is
    # just spam, but there are large enough Spanish-speaking subreddits.
    'reddit': ['en', 'es'],
    'subtlex': ['en', 'de', 'nl', 'zh']
}

OPUS_LANGUAGE_MAP = {
    'pt-PT': 'pt',
    'pt-BR': 'pt_br',
    'zh-Hans': 'zh_cn',
    'zh-Hant': 'zh_tw',
}
WP_LANGUAGE_MAP = {
    'nb': 'no',
}
WP_VERSION = '20161120'

rule all:
    input:
        expand(
            "data/tokenized/opensubtitles/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['opensubtitles']
        ),
        expand(
            "data/tokenized/wikipedia/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['wikipedia'],
        ),
        expand(
            "data/tokenized/europarl/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['europarl'],
            version=[WP_VERSION]
        ),



# Downloaders
# ===========

rule download_opensubtitles_monolingual:
    output:
        "data/downloaded/opensubtitles/{lang}.opus.tar.gz"
    run:
        source_lang = OPUS_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shell("curl -L 'http://opus.lingfil.uu.se/download.php?f=OpenSubtitles2016/{source_lang}.tar.gz' -o {output}")
    resources:
        download=1, opusdownload=1
    priority: 0

rule download_wikipedia:
    output:
        "data/downloaded/wikipedia/wikipedia_{lang}.xml.bz2"
    run:
        source_lang = WP_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        version = WP_VERSION
        shell("curl 'ftp://ftpmirror.your.org/pub/wikimedia/dumps/{source_lang}wiki/{version}/{source_lang}wiki-{version}-pages-articles.xml.bz2' -o {output}")
    resources:
        download=1, wpdownload=1
    priority: 0

rule download_europarl_monolingual:
    output:
        "data/downloaded/europarl/{lang}.opus.tar.gz"
    run:
        source_lang = OPUS_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shell("curl -L 'http://opus.lingfil.uu.se/download.php?f=Europarl/{source_lang}.tar.gz' -o {output}")
    resources:
        download=1, opusdownload=1
    priority: 0


# Processing steps
# ================

# Extracting Wikipedia
rule extract_wikipedia:
    input:
        "data/downloaded/wikipedia/wikipedia_{lang}.xml.bz2"
    output:
        "data/tokenized/wikipedia/{lang}.txt"
    shell:
        "bunzip2 -c {input} | wiki2text | xc tokenize -l {wildcards.lang} > {output}"


# Extracting tokens from OPUS XML packages
rule get_opus_tokens:
    input:
        "data/downloaded/{dir}/{lang}.opus.tar.gz"
    output:
        "data/tokenized/{dir}/{lang}.txt"
    shell:
        "tar xf {input} --ignore-command-error --to-command ./scripts/extract-opus.sh > {output}"


# Counting tokens
rule count_tokens:
    input:
        "data/tokenized/{source}/{lang}.txt"
    output:
        "data/counts/{source}/{lang}.txt"
    shell:
        # The pattern that's being kind of buried under miscellaneous
        # configuration is:
        #
        #   sort | uniq -c | sort -nrk 1
        #
        # This groups together matching tokens using 'sort', counts their
        # occurrences with 'uniq -c', then sorts in numerical reverse order
        # (-nr) by the first column (-k 1), so that the highest counts
        # come first.
        #
        # I use this pattern a lot. It's really useful. Now here are the
        # changes to make to it:
        #
        # - Adding the -d flag to uniq skips things that only occur once,
        #   so the minimum count becomes 2.
        #
        # - Setting LANG=C on the first 'sort' and 'uniq' makes them faster,
        #   as they'll compare UTF-8 bytes instead of trying to do a
        #   full-blown Unicode sort.
        #
        # - Sorting creates a lot of temporary data that could fill up your
        #   /tmp. At least in my case, the data/ directory is on an external
        #   HD that can handle a lot more data, so let's make sure data/tmp
        #   exists and use that as the tmp directory.
        "mkdir -p data/tmp && LANG=C sort -T data/tmp {input} | LANG=C uniq -cd | sort -nrk 1 > {output}"

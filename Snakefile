#!/usr/bin/env python3
# The above line is a lie, but it's close enough to the truth to make syntax
# highlighting happen. Snakemake syntax is an extension of Python 3 syntax.
from exquisite_corpus.tokens import CLD2_REASONABLE_LANGUAGES


SUPPORTED_LANGUAGES = {
    # OPUS's data files of OpenSubtitles 2016
    #
    # Include languages with at least 500 subtitle files, but skip:
    # - 'ze' because that's not a real language code
    #   (it seems to represent code-switching Chinese and English)
    # - 'th' because we don't know how to tokenize it
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
    'reddit': ['en', 'es', 'fr', 'de', 'sv'],

    # Twitter 2014-2015, in all the languages we detect
    'twitter': CLD2_REASONABLE_LANGUAGES,

    # Get data from SUBTLEX in languages where it doesn't seem to overlap
    # too much with OpenSubtitles.
    'subtlex': ['en', 'de', 'nl', 'zh'],

    # NewsCrawl 2014, from the EMNLP Workshops on Statistical Machine Translation
    'newscrawl': ['en', 'fr', 'fi', 'de', 'cs', 'ru'],

    # Google Ngrams 2012
    'google-ngrams': ['en', 'zh-Hans', 'fr', 'de', 'he', 'it', 'ru', 'es'],

    # Jieba's built-in wordlist
    'jieba': ['zh'],

    # Leeds
    'leeds': ['ar', 'de', 'el', 'en', 'es', 'fr', 'it', 'ja', 'pt', 'ru', 'zh'],

    # The Hungarian Webcorpus by Halácsy et al., from http://mokk.bme.hu/resources/webcorpus/
    'mokk': ['hu'],

    # SUBTLEX: word counts from subtitles
    'subtlex': ['en-US', 'en-GB', 'de', 'nl', 'pl', 'zh-Hans'],
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
GOOGLE_LANGUAGE_MAP = {
    'en': 'eng',
    'zh-Hans': 'chi-sim',
    'fr': 'fre',
    'de': 'ger',
    'he': 'heb',
    'it': 'ita',
    'ru': 'rus',
    'es': 'spa'
}
GOOGLE_1GRAM_SHARDS = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e',
    'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'other',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
]
REDDIT_SHARDS = ['{:04d}-{:02d}'.format(y, m) for (y, m) in (
    [(2007, month) for month in range(10, 12 + 1)] +
    [(year, month) for year in range(2008, 2015) for month in range(1, 12 + 1)] +
    [(2015, month) for month in range(1, 5 + 1)]
)]

rule all:
    input:
        expand(
            "data/counts/opensubtitles/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['opensubtitles']
        ),
        expand(
            "data/counts/wikipedia/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['wikipedia'],
        ),
        expand(
            "data/counts/europarl/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['europarl'],
        ),
        expand(
            "data/counts/newscrawl/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['newscrawl']
        ),
        expand(
            "data/counts/google/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['google-ngrams']
        ),
        expand(
            "data/counts/reddit/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['reddit']
        ),
        expand(
            "data/counts/twitter/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['twitter']
        ),
        expand(
            "data/counts/leeds/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['leeds']
        ),
        expand(
            "data/counts/subtlex/{lang}.txt",
            lang=SUPPORTED_LANGUAGES['subtlex']
        ),
        "data/counts/jieba/zh.txt",
        "data/counts/mokk/hu.txt"


# Downloaders
# ===========

rule download_opensubtitles_monolingual:
    output:
        "data/downloaded/opensubtitles/{lang}.txt.gz"
    run:
        source_lang = OPUS_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shell("curl -L 'http://opus.lingfil.uu.se/download.php?f=OpenSubtitles2016/mono/OpenSubtitles2016.raw.{source_lang}.gz' -o {output}")
    resources:
        download=1, opusdownload=1
    priority: 0

rule download_europarl_monolingual:
    output:
        "data/downloaded/europarl/{lang}.txt"
    run:
        source_lang = OPUS_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shell("curl -L 'http://opus.lingfil.uu.se/download.php?f=Europarl/mono/Europarl.raw.{source_lang}.gz' | zcat > {output}")
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

rule download_newscrawl:
    output:
        "data/downloaded/newscrawl-2014-monolingual.tar.gz"
    shell:
        "curl -L 'http://www.statmt.org/wmt15/training-monolingual-news-2014.tgz' -o {output}"

rule download_google:
    output:
        "data/downloaded/google/1grams-{lang}-{shard}.txt.gz"
    run:
        source_lang = GOOGLE_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shard = wildcards.shard
        if source_lang == 'heb' and shard == 'other':
            # This file happens not to exist
            shell("echo -n '' | gzip -c > {output}")
        else:
            # Do a bit of pre-processing as we download
            shell("curl -L 'http://storage.googleapis.com/books/ngrams/books/googlebooks-{source_lang}-all-1gram-20120701-{shard}.gz' | zcat | cut -f 1,3 | gzip -c > {output}")

# Handling downloaded data
# ========================
rule extract_newscrawl:
    input:
        "data/downloaded/newscrawl-2014-monolingual.tar.gz"
    output:
        expand("data/extracted/newscrawl/training-monolingual-news-2014/news.2014.{lang}.shuffled", lang=SUPPORTED_LANGUAGES['newscrawl'])
    shell:
        "tar xf {input} -C data/extracted/newscrawl && touch data/extracted/newscrawl/training-monolingual-news-2014/*"

rule extract_google:
    input:
        expand("data/downloaded/google/1grams-{{lang}}-{shard}.txt.gz",
               shard=GOOGLE_1GRAM_SHARDS)
    output:
        "data/messy-counts/google/{lang}.txt"
    shell:
        # Lowercase the terms, remove part-of-speech tags such as _NOUN, and
        # run the result through the 'countmerge' utility
        r"zcat {input} | sed -n -e 's/\([^_	]\+\)\(_[A-Z]\+\)/\L\1/p' | countmerge > {output}"

rule extract_reddit:
    input:
        "data/raw/reddit/{year}/RC_{year}-{month}.bz2"
    output:
        "data/extracted/reddit/{year}-{month}.txt.gz"
    shell:
        "bunzip2 -c {input} | jq -r 'select(.score > 0) | .body' | fgrep -v '[deleted]' | sed -e 's/&gt;/>/g' -e 's/&lt;/</g' -e 's/&amp;/\&/g' | gzip -c > {output}"

# Transforming existing word lists
# ================================
# To convert the Leeds corpus, look for space-separated lines that start with
# an integer and a decimal. The integer is the rank, which we discard. The
# decimal is the frequency, and the remaining text is the term. Use sed -n
# with /p to output only lines where the match was successful.
#
# The decimals all have 2 digits after the decimal point; we drop the decimal
# point to effectively multiply them by 100 and get integers.
#
# Grep out the term "EOS", an indication that Leeds used MeCab and didn't
# strip out the EOS lines.

rule transform_leeds:
    input:
        "data/source-lists/leeds/internet-{lang}-forms.num"
    output:
        "data/messy-counts/leeds/{lang}.txt"
    shell:
        "sed -rn -e 's/([0-9]+) ([0-9]+).([0-9][0-9]) (.*)/\\4\t\\2\\3/p' {input} | grep -v 'EOS\t' > {output}"

# The Mokk corpus comes from scraping all known .hu Web sites and filtering
# the results for whether they seemed to actually be Hungarian. The list
# contains different counts at different levels of filtering; we choose the
# second-strictest level, which is in the 4th tab-separated field.

rule transform_mokk:
    input:
        "data/source-lists/mokk/web2.2-freq-sorted.txt"
    output:
        "data/messy-counts/mokk/hu.txt"
    shell:
        "iconv -f iso-8859-2 -t utf-8 {input} | cut -f 1,4 > {output}"

# SUBTLEX is different in each instance.
# The main issue with German is that it's mostly (but not entirely) in
# double-UTF-8.
rule transform_subtlex_de:
    input:
        "data/source-lists/subtlex/subtlex.de.txt"
    output:
        "data/messy-counts/subtlex/de.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,3 | ftfy > {output}"

rule transform_subtlex_en:
    input:
        "data/source-lists/subtlex/subtlex.en-{region}.txt"
    output:
        "data/messy-counts/subtlex/en-{region}.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,2 > {output}"

rule transform_subtlex_nl:
    input:
        "data/source-lists/subtlex/subtlex.nl.txt"
    output:
        "data/messy-counts/subtlex/nl.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,2 > {output}"

rule transform_subtlex_pl:
    input:
        "data/source-lists/subtlex/subtlex.pl.txt"
    output:
        "data/messy-counts/subtlex/pl.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,5 > {output}"

rule transform_subtlex_zh:
    input:
        "data/source-lists/subtlex/subtlex.zh.txt"
    output:
        "data/messy-counts/subtlex/zh-Hans.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,5 > {output}"

rule transform_jieba:
    input:
        "data/source-lists/jieba/dict.txt.big"
    output:
        "data/messy-counts/jieba/zh.txt"
    shell:
        "cut -d ' ' -f 1,2 {input} | tr ' ' '    ' | xc simplify-chinese - {output}"

# Tokenizing
# ==========

rule tokenize_wikipedia:
    input:
        "data/downloaded/wikipedia/wikipedia_{lang}.xml.bz2"
    output:
        "data/tokenized/wikipedia/{lang}.txt"
    shell:
        "bunzip2 -c {input} | wiki2text | xc tokenize -l {wildcards.lang} > {output}"

rule tokenize_europarl:
    input:
        "data/downloaded/europarl/{lang}.txt"
    output:
        "data/tokenized/europarl/{lang}.txt"
    shell:
        # Remove country codes and fix mojibake
        "sed -e 's/([A-Z][A-Z]\+)//g' {input} | ftfy | xc tokenize -l {wildcards.lang} > {output}"

rule tokenize_text_newscrawl:
    input:
        "data/extracted/newscrawl/training-monolingual-news-2014/news.2014.{lang}.shuffled"
    output:
        "data/tokenized/newscrawl/{lang}.txt"
    shell:
        "xc tokenize {input} {output} -l {wildcards.lang}"

rule tokenize_gzipped_text:
    input:
        "data/downloaded/{dir}/{lang}.txt.gz"
    output:
        "data/tokenized/{dir}/{lang}.txt"
    shell:
        "zcat {input} | xc tokenize -l {wildcards.lang} > {output}"

rule tokenize_reddit:
    input:
        expand("data/extracted/reddit/{date}.txt.gz", date=REDDIT_SHARDS)
    output:
        expand("data/tokenized/reddit/{{date}}/{lang}.txt", lang=SUPPORTED_LANGUAGES['reddit'])
    shell:
        "zcat {input} | xc tokenize_by_language -m reddit - data/tokenized/reddit"

rule tokenize_twitter:
    input:
        "data/raw/twitter/twitter-2014.txt.gz",
        "data/raw/twitter/twitter-2015.txt.gz"
    output:
        expand("data/tokenized/twitter/{lang}.txt", lang=SUPPORTED_LANGUAGES['twitter'])
    shell:
        "zcat {input} | xc tokenize_by_language -m twitter - data/tokenized/twitter"


# Counting tokens
# ===============
rule count_reddit_tokens:
    input:
        expand("data/tokenized/reddit/{date}/{{lang}}.txt", date=REDDIT_SHARDS)
    output:
        "data/counts/reddit/{lang}.txt"
    shell:
        "cat {input} | xc count - {output}"

rule count_tokens:
    input:
        "data/tokenized/{source}/{lang}.txt"
    output:
        "data/counts/{source}/{lang}.txt"
    shell:
        "xc count {input} {output}"

rule recount_messy_tokens:
    input:
        "data/messy-counts/{source}/{lang}.txt"
    output:
        "data/counts/{source}/{lang}.txt"
    shell:
        "xc recount {input} {output} -l {wildcards.lang}"


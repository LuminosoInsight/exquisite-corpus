#!/usr/bin/env python3
# The above line is a lie, but it's close enough to the truth to make syntax
# highlighting happen. Snakemake syntax is an extension of Python 3 syntax.
from exquisite_corpus.tokens import CLD2_LANGUAGES
from collections import defaultdict


SOURCE_LANGUAGES = {
    # OPUS's data files of OpenSubtitles 2018
    #
    # Include languages with at least 400 subtitle files, but skip:
    # - 'ze' because that's not a real language code
    #   (it seems to represent code-switching Chinese and English)
    # - 'th' because we don't know how to tokenize it
    'opensubtitles': [
        'ar', 'bg', 'bn', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'eu',
        'fa', 'fi', 'fr', 'gl', 'he', 'hr', 'hu', 'id', 'is', 'it', 'ja', 'ko', 'lt',
        'lv', 'mk', 'ml', 'ms',
        'nl', 'nb', 'pl', 'pt-PT', 'pt-BR', 'pt', 'ro', 'ru', 'sh', 'si', 'sk',
        'sl', 'sq', 'sv', 'tr', 'uk', 'vi', 'zh-Hans', 'zh-Hant', 'zh'
    ],

    # Europarl v7, which also comes from OPUS
    'europarl': [
        'bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr', 'hu', 'it',
        'lt', 'lv', 'nl', 'pl', 'pt-PT', 'pt', 'ro', 'sk', 'sl', 'sv'
    ],

    # Tatoeba 2014, from OPUS -- languages with over 50,000 tokens.
    # Skip 'ber' (we don't have the ability to sort out the dialects and
    # scripts of Berber and Tamazight) and 'tlh' (Klingon is not useful enough
    # for the tokenization code it would require).
    'tatoeba': [
        'en', 'eo', 'de', 'fr', 'es', 'ja', 'ru', 'tr', 'it', 'pt', 'he',
        'pl', 'zh-Hans', 'zh', 'hu', 'nl', 'uk', 'fi', 'mn', 'fa', 'ar',
        'da', 'sv', 'bg', 'ia', 'is', 'nb', 'la', 'el', 'fil', 'lt', 'jbo',
        'sh'
    ],

    # Sufficiently large, non-spammy Wikipedias.
    # See https://meta.wikimedia.org/wiki/List_of_Wikipedias -- we're looking
    # for Wikipedias that have at least 100,000 articles and a "depth" measure
    # of 20 or more (indicating that they're not mostly written by bots).
    # Some Wikipedias with a depth of 10 or more are grandfathered into this list.
    'wikipedia': [
        'ar', 'bg', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'en', 'eo', 'es', 'et',
        'eu', 'fa', 'fi', 'fr', 'gl', 'he', 'hi', 'hu', 'hr', 'hy', 'id', 'it',
        'ja', 'ka', 'ko', 'la', 'lt', 'lv', 'ms', 'nn', 'nb', 'nl', 'pl', 'pt',
        'ro', 'ru', 'sh', 'sk', 'sl', 'sv', 'th', 'tr', 'uk', 'ur', 'uz', 'vi',
        'zh',

        # Smaller but high-quality, high-depth Wikipedias
        'mk', 'my', 'te', 'ml', 'bn', 'mr', 'is', 'ku', 'mn', 'si', 'or'
    ],

    # 99.2% of Reddit is in English. Some text that's in other languages is
    # just spam, but these languages seem to have a reasonable amount of
    # representative text.
    #
    # Frequently-detected languages that are too spammy or mis-detected:
    # ar, da, nl, sh, ro, ru, fil
    'reddit/merged': [
        'en', 'es', 'fr', 'de', 'it', 'sv', 'nb', 'fi', 'pl', 'uk', 'hi',
        'ja', 'eo'
    ],

    # Skip Greek because of kaomoji, Simplified Chinese because it's largely
    # spam, Macedonian because of confusability with Bulgarian
    'twitter': [
        'en', 'ar', 'ja', 'ru', 'es', 'tr', 'id', 'pt', 'ko', 'fr', 'ms',
        'it', 'de', 'nl', 'pl', 'hi', 'fil', 'uk', 'sh',
        'ca', 'ta', 'gl', 'fa', 'ne', 'ur', 'he', 'da', 'fi', 'zh-Hant',
        'mn', 'su', 'bn', 'lv', 'jv', 'nb', 'bg', 'cs', 'ro', 'hu',
        'sv', 'sw', 'vi', 'az', 'sq'
    ],

    # GlobalVoices (LREC 2012), from OPUS -- languages with over 500,000 tokens
    'globalvoices': [
        'ar', 'bn', 'ca', 'de', 'en', 'es', 'fr', 'it', 'mg', 'mk', 'nl',
        'pl', 'pt', 'ru', 'sw', 'zh-Hans', 'zh-Hant', 'zh'
    ],

    # NewsCrawl 2014, from the EMNLP Workshops on Statistical Machine Translation
    'newscrawl': ['en', 'fr', 'fi', 'de', 'cs', 'ru'],

    # Google Ngrams 2012
    'google': ['en', 'zh-Hans', 'zh', 'fr', 'de', 'he', 'it', 'ru', 'es'],

    # Jieba's built-in wordlist
    'jieba': ['zh'],

    # Leeds
    'leeds': ['ar', 'de', 'el', 'en', 'es', 'fr', 'it', 'ja', 'pt', 'ru', 'zh'],

    # The Hungarian Webcorpus by Halácsy et al., from http://mokk.bme.hu/resources/webcorpus/
    'mokk': ['hu'],

    # SUBTLEX: word counts from subtitles
    'subtlex': ['en-US', 'en-GB', 'en', 'de', 'nl', 'pl', 'zh-Hans', 'zh'],

    # Amazon reviews (US only)
    'amazon-snap': ['en'],

    # Amazon reviews in other languages
    'amazon-acl10': ['ja', 'de', 'fr'],

    # Voice of America news is translated into different languages. Here's Persian.
    'voa': ['fa'],

    # GlobalVoices and NewsCrawl can be merged into 'news'
    'news': [
        'ar', 'bn', 'ca', 'cs', 'de', 'en', 'es', 'fi', 'fr', 'it', 'mg',
        'mk', 'nl', 'pl', 'pt', 'ru', 'sw', 'zh-Hans', 'zh-Hant', 'zh'
    ],

    # OpenSubtitles and SUBTLEX can be merged into 'subtitles'
    'subtitles': [
        'ar', 'bg', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'fa', 'fi',
        'fr', 'he', 'hr', 'hu', 'id', 'is', 'it', 'ja', 'ko', 'lt', 'mk', 'ms',
        'nl', 'nb', 'pl', 'pt', 'ro', 'ru', 'sh', 'si', 'sk', 'sl', 'sq', 'sv',
        'tr', 'uk', 'zh-Hans', 'zh-Hant', 'zh'
    ],
}

COUNT_SOURCES = [
    'subtitles', 'news', 'wikipedia', 'reddit/merged', 'twitter',
    'google', 'jieba', 'leeds', 'mokk'
]

FULL_TEXT_SOURCES = [
    'wikipedia', 'reddit/merged', 'twitter', 'opensubtitles', 'tatoeba',
    'newscrawl', 'europarl', 'globalvoices'
]
MERGED_SOURCES = {
    'news': ['newscrawl', 'globalvoices', 'voa'],
    'subtitles': ['opensubtitles', 'subtlex'],
    'amazon': ['amazon-snap', 'amazon-acl10']
}
OPUS_LANGUAGE_MAP = {
    'pt-PT': 'pt',
    'pt-BR': 'pt_br',
    'zh-Hans': 'zh_cn',
    'zh-Hant': 'zh_tw',
    'nb': 'no',
}
# GlobalVoices has three made-up language codes, plus 'sr' which we want to
# handle as part of 'sh'.
GLOBALVOICES_LANGUAGE_MAP = {
    'ja': 'jp',
    'zh-Hant': 'zht',
    'zh-Hans': 'zhs',
    'sh': 'sr'
}
TATOEBA_LANGUAGE_MAP = {
    'zh-Hans': 'cmn',
    'fa': 'pes',
    'fil': 'tl',
    'sh': 'sr'
}
WP_LANGUAGE_MAP = {
    'fil': 'tl',
    'nb': 'no'
}
WP_VERSION = '20170420'
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

# These are the shard names for Google Books 2grams data, which I'm interested
# in using as evidence about interesting phrases. I'm skipping numbers and
# 'other' for now; the remaining files are split by the two-letter prefix of
# the first word.
#
# All such prefixes except for 'zq' exist in the English Fiction set. This
# list will have to be adapted as we use other languages or data sets.
GOOGLE_2GRAM_SHARDS = [
    _c1 + _c2
    for _c1 in 'abcdefghijklmnopqrstuvwxyz'
    for _c2 in 'abcdefghijklmnopqrstuvwxyz_'
    if _c1 + _c2 != 'zq'
]
GOOGLE_3GRAM_SHARDS = [
    _c1 + _c2
    for _c1 in 'abcdefghijklmnopqrstuvwxyz'
    for _c2 in 'abcdefghijklmnopqrstuvwxyz_'
    if _c1 + _c2 not in {'qg', 'qz', 'xg', 'xq', 'zq'}
]
REDDIT_SHARDS = ['{:04d}-{:02d}'.format(y, m) for (y, m) in (
    [(2007, month) for month in range(10, 12 + 1)] +
    [(year, month) for year in range(2008, 2015) for month in range(1, 12 + 1)] +
    [(2015, month) for month in range(1, 5 + 1)]
)]
AMAZON_CATEGORIES = [
    'Books', 'Electronics', 'Movies_and_TV', 'CDs_and_Vinyl',
    'Clothing_Shoes_and_Jewelry', 'Home_and_Kitchen', 'Kindle_Store',
    'Sports_and_Outdoors', 'Cell_Phones_and_Accessories', 'Health_and_Personal_Care',
    'Toys_and_Games', 'Video_Games', 'Tools_and_Home_Improvement', 'Beauty',
    'Apps_for_Android', 'Office_Products', 'Pet_Supplies', 'Automotive',
    'Grocery_and_Gourmet_Food', 'Patio_Lawn_and_Garden', 'Baby', 'Digital_Music',
    'Musical_Instruments', 'Amazon_Instant_Video'
]
AMAZON_ACL_DATASETS = [
    'books/train', 'books/unlabeled', 'music/train', 'music/unlabeled',
    'dvd/train', 'dvd/unlabeled'
]
# The language-country-wtf codes that the ACL10 Amazon sentiment data uses.
# 'jp' is a country code, and we need to change it to 'ja' in a later step.
AMAZON_ACL_CODES = ['en', 'de', 'fr', 'jp']

LANGUAGE_SOURCES = defaultdict(list)
for source in COUNT_SOURCES:
    for _lang in SOURCE_LANGUAGES[source]:
        LANGUAGE_SOURCES[_lang].append(source)

# Determine which languages we can support and which languages we can build a
# full-size list for. We want to have sources from 5 different registers of
# language to build a full list, but we give Dutch a pass -- it used to have 5
# sources before we took out Common Crawl and considered OpenSubtitles and
# SUBTLEX to count as the same source.
SUPPORTED_LANGUAGES = sorted([_lang for _lang in LANGUAGE_SOURCES if len(LANGUAGE_SOURCES[_lang]) >= 3])
LARGE_LANGUAGES = sorted([_lang for _lang in LANGUAGE_SOURCES if len(LANGUAGE_SOURCES[_lang]) >= 5 or _lang == 'nl'])
TWITTER_LANGUAGES = sorted(set(SOURCE_LANGUAGES['twitter']) & set(SUPPORTED_LANGUAGES))
PARALLEL_LANGUAGES = ['ar', 'de', 'en', 'es', 'fa', 'fi', 'fr', 'it', 'ja', 'nl', 'pl', 'pt', 'ru', 'sv', 'zh-Hans', 'zh-Hant', 'zh']
LANGUAGE_PAIRS = [
    "{}-{}".format(_lang1, _lang2)
    for _lang1 in PARALLEL_LANGUAGES for _lang2 in PARALLEL_LANGUAGES
    if _lang1 < _lang2
]


def language_count_sources(lang):
    """
    Get all the sources of word counts we have in a language.
    """
    return [
        "data/counts/{source}/{lang}.txt".format(source=source, lang=lang)
        for source in LANGUAGE_SOURCES[lang]
    ]


def language_text_sources(lang):
    """
    Get all the sources of tokenized text we have in a language.
    """
    return [
        "data/tokenized/{source}/{lang}.txt".format(source=source, lang=lang)
        for source in LANGUAGE_SOURCES[lang]
        if source in FULL_TEXT_SOURCES
    ]

def multisource_counts_to_merge(multisource, lang):
    """
    Given a multi-source name like 'news' and a language code, find which sources
    of counts should be merged to produce it.
    """
    return [
        "data/counts/{source}/{lang}.txt".format(source=source, lang=lang)
        for source in MERGED_SOURCES[multisource]
        if lang in SOURCE_LANGUAGES[source]
    ]

def balkanize_cld2_languages(languages):
    """
    CLD2 detects 'sr', 'hr', and 'bs' separately, and outputs them in
    separate files that we'll have to merge together, because it's not actually
    reliably distinguishing them.
    """
    result = set()
    for lang in languages:
        if lang == 'sh':
            result.update(['sr', 'hr', 'bs'])
        else:
            result.add(lang)
    return sorted(result)


# Top-level rules
# ===============

rule wordfreq:
    input:
        expand("data/wordfreq/combined_{lang}.msgpack.gz", lang=SUPPORTED_LANGUAGES),
        expand("data/wordfreq/large_{lang}.msgpack.gz", lang=LARGE_LANGUAGES),
        expand("data/wordfreq/twitter_{lang}.msgpack.gz", lang=TWITTER_LANGUAGES),
        "data/wordfreq/jieba_zh.txt"

rule parallel:
    input:
        "data/interspersed/shuffled.txt"

rule frequencies:
    input:
        expand("data/freqs/{lang}.txt", lang=SUPPORTED_LANGUAGES)

rule embeddings:
    input:
        expand("data/skipgrams/{lang}.vec", lang=LARGE_LANGUAGES)

rule google_2grams:
    input:
        expand("data/downloaded/google-ngrams/2grams-en-{shard}.txt.gz", shard=GOOGLE_2GRAM_SHARDS)

rule google_3grams:
    input:
        expand("data/downloaded/google-ngrams/3grams-en-{shard}.txt.gz", shard=GOOGLE_3GRAM_SHARDS)


# Downloaders
# ===========

rule download_opensubtitles_monolingual:
    output:
        "data/downloaded/opensubtitles/{lang}.txt.gz"
    run:
        source_lang = OPUS_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shell("curl -L 'http://opus.nlpl.eu/download.php?f=OpenSubtitles2018/mono/OpenSubtitles2018.raw.{source_lang}.gz' -o {output}")
    resources:
        download=1, opusdownload=1
    priority: 0

rule download_opensubtitles_parallel:
    output:
        "data/downloaded/opensubtitles/{lang1}-{lang2}.zip"
    shell:
        "curl -L 'http://opus.lingfil.uu.se/download.php?f=OpenSubtitles2018/{wildcards.lang1}-{wildcards.lang2}.txt.zip' -o {output}"

rule download_europarl_monolingual:
    output:
        "data/downloaded/europarl/{lang}.txt"
    run:
        source_lang = OPUS_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shell("curl -L 'http://opus.lingfil.uu.se/download.php?f=Europarl/mono/Europarl.raw.{source_lang}.gz' | zcat > {output}")
    resources:
        download=1, opusdownload=1
    priority: 0

rule download_globalvoices_monolingual:
    output:
        "data/downloaded/globalvoices/{lang}.txt"
    run:
        source_lang = GLOBALVOICES_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shell("curl -L 'http://opus.lingfil.uu.se/download.php?f=GlobalVoices/mono/GlobalVoices.raw.{source_lang}.gz' | zcat > {output}")
    resources:
        download=1, opusdownload=1
    priority: 0

rule download_tatoeba_monolingual:
    output:
        "data/downloaded/tatoeba/{lang}.txt"
    run:
        source_lang = TATOEBA_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shell("curl -L 'http://opus.lingfil.uu.se/download.php?f=Tatoeba/mono/Tatoeba.raw.{source_lang}.gz' | zcat > {output}")
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

rule download_google_1grams:
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

rule download_google_ngrams:
    output:
        "data/downloaded/google-ngrams/{n}grams-{lang}-{shard}.txt.gz"
    run:
        source_lang = GOOGLE_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shard = wildcards.shard
        n = wildcards.n
        # Do a bit of pre-processing as we download
        shell("curl -L 'http://storage.googleapis.com/books/ngrams/books/googlebooks-{source_lang}-fiction-all-{n}gram-20120701-{shard}.gz' | zcat | cut -f 1,3 | gzip -c > {output}")

rule download_amazon_snap:
    output:
        "data/downloaded/amazon/{category}.json.gz"
    shell:
        "curl -L 'http://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_{wildcards.category}_5.json.gz' -o {output}"

rule download_amazon_acl10:
    output:
        "data/downloaded/amazon/cls-acl10-unprocessed.tar.gz"
    shell:
        "curl -L 'http://www.uni-weimar.de/medien/webis/corpora/corpus-webis-cls-10/cls-acl10-unprocessed.tar.gz' -o {output}"


# Handling downloaded data
# ========================
rule extract_opensubtitles_parallel:
    input:
        "data/downloaded/opensubtitles/{lang1}-{lang2}.zip"
    output:
        "data/extracted/opensubtitles/OpenSubtitles2018.{lang1}-{lang2}.{lang1}",
        "data/extracted/opensubtitles/OpenSubtitles2018.{lang1}-{lang2}.{lang2}"
    shell:
        "unzip -o -d 'data/extracted/opensubtitles/' {input} && touch {output}"

rule extract_newscrawl:
    input:
        "data/downloaded/newscrawl-2014-monolingual.tar.gz"
    output:
        expand("data/extracted/newscrawl/training-monolingual-news-2014/news.2014.{lang}.shuffled", lang=SOURCE_LANGUAGES['newscrawl'])
    shell:
        "tar xf {input} -C data/extracted/newscrawl && touch data/extracted/newscrawl/training-monolingual-news-2014/*"

rule extract_amazon_acl10:
    input:
        "data/downloaded/amazon/cls-acl10-unprocessed.tar.gz"
    output:
        expand("data/extracted/amazon-acl10/cls-acl10-unprocessed/{lang}/{dataset}.review",
               lang=AMAZON_ACL_CODES,
               dataset=AMAZON_ACL_DATASETS)
    shell:
        "tar xf {input} -C data/extracted/amazon-acl10 && touch {output}"

rule extract_google_1grams:
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

rule extract_amazon:
    input:
        "data/downloaded/amazon/{category}.json.gz"
    output:
        "data/extracted/amazon-snap/{category}.csv"
    shell:
        r"""zcat {input} | jq -r -c '"label__\(.["overall"] | tostring)\t\(.["summary"])\t\(.["reviewText"])"' > {output}"""

rule extract_voa_fa:
    input:
        "data/extra/voa_fa_2003-2008_orig.txt"
    output:
        "data/extracted/voa/fa.txt"
    shell:
        "sed -e 's/^# Headline: //' -e 's/^#.*//' {input} > {output}"



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

# The Mokk Hungarian Web corpus comes from scraping all known .hu Web sites and
# filtering the results for whether they seemed to actually be Hungarian. The
# list contains different counts at different levels of filtering; we choose
# the second most permissive level, which is in the 3rd tab-separated field.

rule transform_mokk:
    input:
        "data/source-lists/mokk/web2.2-freq-sorted.txt"
    output:
        "data/messy-counts/mokk/hu.txt"
    shell:
        "iconv -f iso-8859-2 -t utf-8 {input} | cut -f 1,3 > {output}"

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
        "cut -d ' ' -f 1,2 {input} | tr ' ' '\t' | xc simplify-chinese - {output}"

rule transform_2grams:
    input:
        "data/downloaded/google-ngrams/2grams-{lang}-{prefix}.txt.gz"
    output:
        "data/messy-counts/google-ngrams/2grams-{lang}-{prefix}.txt"
    shell:
        r"zcat {input} | sed -re 's/_[A-Z.]*//g' | tr A-Z a-z | countmerge > {output}"

rule transform_3grams:
    input:
        "data/downloaded/google-ngrams/3grams-{lang}-{prefix}.txt.gz"
    output:
        "data/messy-counts/google-ngrams/3grams-{lang}-{prefix}.txt"
    shell:
        r"zcat {input} | sed -re 's/_[A-Z.]*//g' | tr A-Z a-z | countmerge > {output}"

rule concat_2grams:
    input:
        expand("data/messy-counts/google-ngrams/2grams-en-{prefix}.txt", prefix=GOOGLE_2GRAM_SHARDS)
    output:
        "data/messy-counts/google-ngrams/2grams-combined-en.txt.gz"
    shell:
        "grep -Eh '[0-9]{{3,}}$' {input} | LANG=C sort | countmerge | gzip -c > {output}"

rule concat_3grams:
    input:
        expand("data/messy-counts/google-ngrams/3grams-en-{prefix}.txt", prefix=GOOGLE_3GRAM_SHARDS)
    output:
        "data/messy-counts/google-ngrams/3grams-combined-en.txt.gz"
    shell:
        "grep -Eh '[0-9]{{3,}}$' {input} | LANG=C sort | countmerge | gzip -c > {output}"


# Tokenizing
# ==========

rule tokenize_wikipedia:
    input:
        "data/downloaded/wikipedia/wikipedia_{lang}.xml.bz2"
    output:
        "data/tokenized/wikipedia/{lang}.txt"
    shell:
        "bunzip2 -c {input} | wiki2text | xc tokenize -l {wildcards.lang} - {output}"

rule tokenize_amazon:
    input:
        expand("data/extracted/amazon-snap/{category}.csv", category=AMAZON_CATEGORIES)
    output:
        expand("data/tokenized/amazon-snap/en.txt")
    shell:
        "sed -e 's/\t/ ¶ /g' {input} | xc tokenize -l en | sed -e 's/label__/__label__/' > {output}"

rule tokenize_europarl:
    input:
        "data/downloaded/europarl/{lang}.txt"
    output:
        "data/tokenized/europarl/{lang}.txt"
    shell:
        # Remove country codes and fix mojibake
        "sed -e 's/([A-Z][A-Z]\+)//g' {input} | ftfy | xc tokenize -l {wildcards.lang} - {output}"

rule tokenize_tatoeba:
    input:
        "data/downloaded/tatoeba/{lang}.txt"
    output:
        "data/tokenized/tatoeba/{lang}.txt"
    shell:
        "xc tokenize -l {wildcards.lang} {input} {output}"

rule tokenize_globalvoices:
    input:
        "data/downloaded/globalvoices/{lang}.txt"
    output:
        "data/tokenized/globalvoices/{lang}.txt"
    shell:
        "sed -e 's/· Global Voices//' {input} | xc tokenize -c -l {wildcards.lang} - {output}"

rule tokenize_newscrawl:
    input:
        "data/extracted/newscrawl/training-monolingual-news-2014/news.2014.{lang}.shuffled"
    output:
        "data/tokenized/newscrawl/{lang}.txt"
    shell:
        "xc tokenize -c -l {wildcards.lang} {input} {output}"

rule tokenize_parallel_opensubtitles:
    input:
        "data/extracted/opensubtitles/OpenSubtitles2018.{langpair}.{lang}"
    output:
        "data/tokenized/opensubtitles/parallel/{langpair}.{lang}.txt"
    shell:
        "xc tokenize -l {wildcards.lang} {input} {output}"

rule parallel_opensubtitles:
    input:
        "data/tokenized/opensubtitles/parallel/{lang1}-{lang2}.{lang1}.txt",
        "data/tokenized/opensubtitles/parallel/{lang1}-{lang2}.{lang2}.txt"
    output:
        "data/parallel/opensubtitles/{lang1}-{lang2}.txt"
    shell:
        "paste {input} > {output}"

rule tokenize_gzipped_text:
    input:
        "data/downloaded/{dir}/{lang}.txt.gz"
    output:
        "data/tokenized/{dir}/{lang}.txt"
    shell:
        "zcat {input} | xc tokenize -l {wildcards.lang} - {output}"

rule tokenize_reddit:
    input:
        "data/extracted/reddit/{date}.txt.gz"
    output:
        expand("data/tokenized/reddit/{{date}}/{lang}.txt", lang=SOURCE_LANGUAGES['reddit/merged'])
    shell:
        "zcat {input} | xc tokenize-by-language -m reddit - data/tokenized/reddit/{wildcards.date}"

rule tokenize_twitter:
    input:
        "data/raw/twitter/twitter-2014.txt.gz",
        "data/raw/twitter/twitter-2015.txt.gz"
    output:
        expand("data/tokenized/twitter/{lang}.txt", lang=SOURCE_LANGUAGES['twitter'])
    shell:
        "zcat {input} | xc tokenize-by-language -m twitter - data/tokenized/twitter"

rule tokenize_voa:
    input:
        "data/extracted/voa/{lang}.txt"
    output:
        "data/tokenized/voa/{lang}.txt"
    shell:
        "xc tokenize -l {wildcards.lang} - {output}"


# Counting tokens
# ===============
rule count_tokens:
    input:
        "data/tokenized/{source}/{lang}.txt"
    output:
        "data/counts/{source}/{lang}.txt"
    shell:
        "xc count {input} {output}"

# Merging frequencies
rule merge_freqs:
    input:
        lambda wildcards: language_count_sources(wildcards.lang)
    output:
        "data/freqs/{lang}.txt"
    shell:
        "xc merge-freqs {input} {output}"

# Counts to frequencies without merging
rule count_to_freqs:
    input:
        "data/counts/{source}/{lang}.txt"
    output:
        "data/freqs/{source}/{lang}.txt"
    shell:
        "xc count-to-freqs {input} {output}"


# Handling overlapping languages
# ==============================

# Reddit has a fair amount of conversation in Serbo-Croatian. cld2 cannot
# actually distinguish what country the speaker is in, so the Latin text
# ends up spread pretty much arbitrarily between Serbian, Croatian, and
# Bosnian. Here, we re-split the data into Latin text (Serbo-Croatian)
# and Cyrillic (Serbian).

# OpenSubtitles is presumably separated by country, but we also want to align
# it with the 'sh' data we have from other sources.
rule debalkanize_opensubtitles_sh:
    input:
        expand("data/tokenized/opensubtitles/{lang}.txt", lang=['bs', 'hr', 'sr'])
    output:
        "data/tokenized/opensubtitles/sh.txt"
    shell:
        "grep -vh '[А-Яа-я]' {input} > {output}"

rule recount_messy_tokens:
    input:
        "data/messy-counts/{source}/{lang}.txt"
    output:
        "data/counts/{source}/{lang}.txt"
    shell:
        "xc recount {input} {output} -l {wildcards.lang}"

rule merge_reddit:
    input:
        expand("data/counts/reddit/{date}/{{lang}}.txt", date=REDDIT_SHARDS)
    output:
        "data/counts/reddit/merged/{lang}.txt"
    shell:
        "cat {input} | xc recount - {output} -l {wildcards.lang}"

rule merge_subtlex_en:
    input:
        "data/counts/subtlex/en-GB.txt",
        "data/counts/subtlex/en-US.txt",
    output:
        "data/counts/subtlex/en.txt"
    shell:
        "cat {input} | xc recount - {output} -l en"

rule merge_opensubtitles_pt:
    input:
        "data/tokenized/opensubtitles/pt-BR.txt",
        "data/tokenized/opensubtitles/pt-PT.txt",
    output:
        "data/tokenized/opensubtitles/pt.txt"
    shell:
        "cat {input} > {output}"

rule merge_opensubtitles_zh:
    input:
        "data/tokenized/opensubtitles/zh-Hans.txt",
        "data/tokenized/opensubtitles/zh-Hant.txt",
    output:
        "data/tokenized/opensubtitles/zh.txt"
    shell:
        "cat {input} | xc simplify-chinese - {output}"

rule merge_globalvoices_zh:
    input:
        "data/tokenized/globalvoices/zh-Hans.txt",
        "data/tokenized/globalvoices/zh-Hant.txt",
    output:
        "data/tokenized/globalvoices/zh.txt"
    shell:
        "cat {input} | xc simplify-chinese > {output}"

rule copy_google_zh:
    input:
        "data/counts/google/zh-Hans.txt"
    output:
        "data/counts/google/zh.txt"
    shell:
        "xc simplify-chinese {input} {output}"

rule copy_tatoeba_zh:
    input:
        "data/tokenized/tatoeba/zh-Hans.txt"
    output:
        "data/tokenized/tatoeba/zh.txt"
    shell:
        "cp {input} {output}"

rule copy_subtlex_zh:
    input:
        "data/counts/subtlex/zh-Hans.txt"
    output:
        "data/counts/subtlex/zh.txt"
    shell:
        "xc simplify-chinese {input} {output}"

rule copy_europarl_pt:
    input:
        "data/tokenized/europarl/pt-PT.txt"
    output:
        "data/tokenized/europarl/pt.txt"
    shell:
        "cp {input} {output}"

# Handling similar data
# =====================

rule merge_news:
    input:
        lambda wildcards: multisource_counts_to_merge('news', wildcards.lang)
    output:
        "data/counts/news/{lang}.txt"
    shell:
        "cat {input} | xc recount - {output} -l {wildcards.lang}"

rule merge_subtitles:
    input:
        lambda wildcards: multisource_counts_to_merge('subtitles', wildcards.lang)
    output:
        "data/counts/subtitles/{lang}.txt"
    shell:
        "cat {input} | xc recount - {output} -l {wildcards.lang}"


# Assembling corpus text
# ======================

rule combine_reddit:
    input:
        expand("data/tokenized/reddit/{date}/{{lang}}.txt", date=REDDIT_SHARDS)
    output:
        "data/tokenized/reddit/merged/{lang}.txt"
    run:
        if wildcards.lang == 'en':
            shell("cat {input} | split -n r/1/50 > {output}")
        else:
            shell("cat {input} > {output}")

rule shuffle_full_text:
    input:
        lambda wildcards: language_text_sources(wildcards.lang)
    output:
        "data/shuffled/{lang}.txt"
    shell:
        "grep -h '.' {input} | scripts/imperfect-shuffle.sh {output} {wildcards.lang}"

rule fasttext_skipgrams:
    input:
        "data/shuffled/{lang}.txt"
    output:
        "data/skipgrams/{lang}.vec",
        "data/skipgrams/{lang}.bin"
    run:
        if wildcards.lang == 'en':
            shell("fasttext skipgram -dim 300 -input {input} -output data/skipgrams/{wildcards.lang}")
        else:
           shell("fasttext skipgram -dim 200 -epoch 20 -input {input} -output data/skipgrams/{wildcards.lang}")


# Making training data from parallel text
# =======================================

rule intersperse_parallel:
    input:
        "data/parallel/{dir}/{lang1}-{lang2}.txt"
    output:
        "data/interspersed/{dir}/{lang1}-{lang2}.txt"
    shell:
        "xc intersperse {input} {output} {wildcards.lang1} {wildcards.lang2}"

rule shuffle_interspersed_parallel:
    input:
        expand("data/interspersed/opensubtitles/{pair}.txt", pair=LANGUAGE_PAIRS)
    output:
        "data/interspersed/shuffled.txt"
    shell:
        "cat {input} | scripts/imperfect-shuffle.sh {output} interspersed"




# Building wordfreq data files
# ============================

rule make_small_wordfreq_list:
    input:
        "data/freqs/{lang}.txt"
    output:
        "data/wordfreq/combined_{lang}.msgpack.gz"
    shell:
        "xc export-to-wordfreq {input} - -c 600 | gzip -c > {output}"

rule make_large_wordfreq_list:
    input:
        "data/freqs/{lang}.txt"
    output:
        "data/wordfreq/large_{lang}.msgpack.gz"
    shell:
        "xc export-to-wordfreq {input} - -c 800 | gzip -c > {output}"

rule make_twitter_wordfreq_list:
    input:
        "data/freqs/twitter/{lang}.txt"
    output:
        "data/wordfreq/twitter_{lang}.msgpack.gz"
    shell:
        "xc export-to-wordfreq {input} - -c 600 | gzip -c > {output}"

rule make_jieba_list:
    input:
        "data/freqs/{lang}.txt"
    output:
        "data/wordfreq/jieba_{lang}.txt"
    shell:
        "xc export-to-jieba {input} {output} -c 600"


ruleorder:
    count_to_freqs > merge_freqs > merge_reddit > \
    merge_subtlex_en > merge_opensubtitles_pt > merge_opensubtitles_zh > merge_globalvoices_zh > \
    merge_news > merge_subtitles > \
    combine_reddit > copy_google_zh > copy_tatoeba_zh > copy_europarl_pt > \
    recount_messy_tokens > count_tokens > \
    tokenize_parallel_opensubtitles > tokenize_gzipped_text


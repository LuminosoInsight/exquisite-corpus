#!/usr/bin/env python3
# The above line is a lie, but it's close enough to the truth to make syntax
# highlighting happen. Snakemake syntax is an extension of Python 3 syntax.

### Languages to add when OSCAR data is included:
# Urdu (ur)
# Nynorsk (nn)
# Slovenian (sl)
# Slovak (sk)
# Estonian (et)
# Albanian (sq)
# Vietnamese (vi)
# Lithuanian (lt)
# Galician (gl)
# Filipino (fil)
# Swahili (sw)
# Basque (eu)
# Icelandic (is)
# Tamil (ta)

import os
from collections import defaultdict

DATA = 'data'
INCLUDE_TWITTER = "EXCLUDE_TWITTER" not in config

SOURCE_LANGUAGES = {
    # OPUS's data files of OpenSubtitles 2018
    #
    # Include languages with at least 400 subtitle files, but skip:
    # - 'ze' because that's not a real language code
    #   (it seems to represent code-switching Chinese and English)
    # - 'th' because we don't know how to tokenize it
    'opus/OpenSubtitles2018': [
        'ar', 'bg', 'bn', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'eu',
        'fa', 'fi', 'fr', 'gl', 'he', 'hr', 'hu', 'id', 'is', 'it', 'ja', 'ko', 'lt',
        'lv', 'mk', 'ml', 'ms',
        'nl', 'nb', 'pl', 'pt-PT', 'pt-BR', 'pt', 'ro', 'ru', 'sh', 'si', 'sk',
        'sl', 'sq', 'sv', 'tr', 'uk', 'vi', 'zh-Hans', 'zh-Hant', 'zh'
    ],

    # Europarl v7, which also comes from OPUS
    'opus/Europarl': [
        'bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr', 'hu', 'it',
        'lt', 'lv', 'nl', 'pl', 'pt-PT', 'pt', 'ro', 'sk', 'sl', 'sv'
    ],

    # Tatoeba 2014, from OPUS -- languages with over 50,000 tokens.
    # Skip 'ber' (we don't have the ability to sort out the dialects and
    # scripts of Berber and Tamazight) and 'tlh' (Klingon is not useful enough
    # for the tokenization code it would require).
    'opus/Tatoeba': [
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

        'ta', 'cy',

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

    # GlobalVoices (LREC 2012), from OPUS -- languages with over 500,000 tokens
    'opus/GlobalVoices': [
        'ar', 'bn', 'ca', 'de', 'en', 'es', 'fr', 'it', 'mg', 'mk', 'nl',
        'pl', 'pt', 'ru', 'sw', 'zh-Hans', 'zh-Hant', 'zh'
    ],

    # NewsCrawl 2014, from the EMNLP Workshops on Statistical Machine Translation
    'newscrawl': ['en', 'fr', 'fi', 'de', 'cs', 'ru'],

    # JESC: parallel English/Japanese subtitles
    'jesc': ['en', 'ja'],

    # Google Ngrams 2012
    'google': ['en', 'zh-Hans', 'zh', 'fr', 'de', 'he', 'it', 'ru', 'es'],

    # Jieba's built-in wordlist
    'jieba': ['zh'],

    # Leeds
    'leeds': ['ar', 'de', 'el', 'en', 'es', 'fr', 'it', 'ja', 'pt', 'ru', 'zh'],

    # The Hungarian Webcorpus by Halácsy et al., from http://mokk.bme.hu/resources/webcorpus/
    'mokk': ['hu'],

    # ParaCrawl, which aligns Web-crawled text from English to 11 other languages
    'paracrawl': [
        'cs', 'de', 'en', 'es', 'fi', 'fr', 'it', 'lv', 'nl', 'pl', 'pt', 'ro'
    ],

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

    # 'web' merges Web-crawled sources: ParaCrawl, Leeds, and Mokk
    'web': [
        'ar', 'cs', 'de', 'el', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja', 'lv',
        'nl', 'pl', 'pt', 'ro', 'ru', 'zh'
    ]
}

COUNT_SOURCES = [
    'subtitles', 'news', 'wikipedia', 'reddit/merged',
    'google', 'jieba', 'web'
]

FULL_TEXT_SOURCES = [
    'wikipedia', 'reddit/merged', 'opensubtitles', 'tatoeba',
    'newscrawl', 'europarl', 'globalvoices'
]
MERGED_SOURCES = {
    'news': ['newscrawl', 'opus/GlobalVoices', 'voa'],
    'web': ['mokk', 'leeds', 'paracrawl'],
    'subtitles': ['opus/OpenSubtitles2018', 'subtlex'],
    'amazon': ['amazon-snap', 'amazon-acl10']
}

if INCLUDE_TWITTER:
    SOURCE_LANGUAGES.update({
        'twitter1': [
            'en', 'ar', 'ja', 'ru', 'es', 'tr', 'id', 'pt', 'ko', 'fr', 'ms',
            'it', 'de', 'nl', 'pl', 'hi', 'fil', 'uk',
            'ca', 'ta', 'gl', 'fa', 'ne', 'ur', 'he', 'da', 'fi', 'zh',
            'mn', 'su', 'bn', 'lv', 'jv', 'nb', 'bg', 'cs', 'hu',
            'sv', 'sw', 'vi', 'az', 'sq', 'el', 'mk'
        ],
        'twitter2': [
            'ar', 'bg', 'bn', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'fa', 'fi',
            'fr', 'he', 'hi', 'hu', 'id', 'it', 'ja', 'ko', 'lv', 'mk', 'ms', 'nb',
            'nl', 'pl', 'pt', 'ru', 'sv', 'tr', 'uk', 'zh'
        ],
        'twitter': [
            'ar', 'bg', 'bn', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'fa', 'fi',
            'fr', 'he', 'hi', 'hu', 'id', 'it', 'ja', 'ko', 'lv', 'mk', 'ms', 'nb',
            'nl', 'pl', 'pt', 'ru', 'sv', 'tr', 'uk', 'zh'
        ]
    })
    COUNT_SOURCES.append('twitter')
    FULL_TEXT_SOURCES.append('twitter')
    MERGED_SOURCES['twitter'] = ['twitter1', 'twitter2']

WP_LANGUAGE_MAP = {
    'fil': 'tl',
    'nb': 'no'
}
WP_VERSION = '20200801'
GOOGLE_LANGUAGE_MAP = {
    'en': 'eng',
    'zh-Hans': 'chi_sim',
    'fr': 'fre',
    'de': 'ger',
    'he': 'heb',
    'it': 'ita',
    'ru': 'rus',
    'es': 'spa'
}

GOOGLE_NUM_1GRAM_SHARDS = {
    'en': 24,
    'zh-Hans': 1,
    'fr': 6,
    'de': 8,
    'he': 1,
    'it': 2,
    'ru': 2,
    'es': 3
}

# Google Books 2012 unigrams are sharded by the first letter or digit of the token,
# or 'other'.
GOOGLE_1GRAM_SHARDS = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e',
    'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'other',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
]

# These are the shard names for Google Books data, which I'm interested in
# using as evidence about interesting phrases. I'm skipping numbers and 'other'
# for now; the remaining files are split by the two-letter prefix of the first
# token.
#
# Unfortunately, the 2-letter prefixes that never occur in any tokens in the
# vocabulary correspond to files that simply don't exist. In order to avoid
# errors, we need to exclude those prefixes: 'zq' from the 2grams, and four
# additional prefixes from 3grams.

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

# We have Reddit data that's sharded by month, from 2007-10 to 2017-11.

REDDIT_SHARDS = ['{:04d}-{:02d}'.format(y, m) for (y, m) in (
    [(2007, month) for month in range(10, 12 + 1)] +
    [(year, month) for year in range(2008, 2020) for month in range(1, 12 + 1)]
)]

# Sample 1 out of every 5 months, which allows us to download fewer files, but
# (because 5 is relatively prime to 12) provides a reasonably even sample of
# events around the year.
SAMPLED_REDDIT_SHARDS = [
    '2007-10', '2008-03', '2008-08', '2009-01', '2009-06', '2009-11',
    '2010-04', '2010-09', '2011-02', '2011-07', '2011-12', '2012-05',
    '2012-10', '2013-03', '2013-08', '2014-01', '2014-06', '2014-11',
    '2015-04', '2015-09', '2015-02', '2016-07', '2016-12', '2017-05',
    '2017-10', '2018-03', '2018-08', '2019-01', '2019-06', '2019-11',
]

TWITTER_V2_YEARS = ['2020']

# SNAP's Amazon data is sharded by product department.

AMAZON_CATEGORIES = [
    'Books', 'Electronics', 'Movies_and_TV', 'CDs_and_Vinyl',
    'Clothing_Shoes_and_Jewelry', 'Home_and_Kitchen', 'Kindle_Store',
    'Sports_and_Outdoors', 'Cell_Phones_and_Accessories', 'Health_and_Personal_Care',
    'Toys_and_Games', 'Video_Games', 'Tools_and_Home_Improvement', 'Beauty',
    'Apps_for_Android', 'Office_Products', 'Pet_Supplies', 'Automotive',
    'Grocery_and_Gourmet_Food', 'Patio_Lawn_and_Garden', 'Baby', 'Digital_Music',
    'Musical_Instruments', 'Amazon_Instant_Video'
]


# The Amazon ACL dataset is split into 'books', 'music', and 'dvd', and also
# separated into labeled training data and unlabeled data.

AMAZON_ACL_DATASETS = [
    'books/train', 'books/unlabeled', 'music/train', 'music/unlabeled',
    'dvd/train', 'dvd/unlabeled'
]

# The language-country-wtf codes that the ACL10 Amazon sentiment data uses.
# 'jp' is a country code, and we need to change it to 'ja' in a later step.

AMAZON_ACL_CODES = ['en', 'de', 'fr', 'jp']

# Sample the datasets and languages in testmode
TESTMODE = bool(os.environ.get("XC_BUILD_TEST"))
if TESTMODE:
    DATA = 'tests/data'
    REDDIT_SHARDS = [
        '2007-10', '2009-09', '2011-01', '2013-12', '2015-08', '2017-02',
    ]
    SOURCE_LANGUAGES['wikipedia'] = [
        'ar', 'bn', 'cs', 'en', 'fr', 'hu', 'it', 'nl', 'pl', 'zh'
    ]
    GOOGLE_1GRAM_SHARDS = [
        '2', 'a', 'e', 'm', 'n', 'p', 's', 'r', 't', 'u', 'other',
    ]

# Create a mapping from language codes to sources that we have for that
# language.

LANGUAGE_SOURCES = defaultdict(list)
for _source in COUNT_SOURCES:
    for _lang in SOURCE_LANGUAGES[_source]:
        LANGUAGE_SOURCES[_lang].append(_source)

# Determine which languages we can support and which languages we can build a
# full-size list for. We want to have sources from 5 different registers of
# language to build a full list, but we give Dutch a pass -- it used to have 5
# sources before we took out Common Crawl and considered OpenSubtitles and
# SUBTLEX to count as the same source.

SUPPORTED_LANGUAGES = sorted([_lang for _lang in LANGUAGE_SOURCES if len(LANGUAGE_SOURCES[_lang]) >= 3])
LARGE_LANGUAGES = sorted([_lang for _lang in LANGUAGE_SOURCES if len(LANGUAGE_SOURCES[_lang]) >= 5 or _lang == 'nl'])


# We'll build a parallel text between English and 14 languages. We construct
# PARALLEL_LANGUAGES and PARALLEL_SOURCES lists manually to be sure that we get the
# codes and sources correctly.

# Parallel language pairs
# zh-x-oversimplified means oversimplified Chinese
PARALLEL_LANGUAGES = [
    'ar_en', 'de_en', 'en_es', 'en_fr', 'en_id', 'en_it', 'en_ja', 'en_ko', 'en_nl',
    'en_pl', 'en_pt', 'en_ru', 'en_sv', 'en_zh-x-oversimplified'
]

PARALLEL_LANGUAGE_PAIRS = []
for pair in PARALLEL_LANGUAGES:
    lang1, lang2 = pair.split('_')
    PARALLEL_LANGUAGE_PAIRS.append("{}_{}".format(lang1, lang2))
    PARALLEL_LANGUAGE_PAIRS.append("{}_{}".format(lang2, lang1))

# Parallel language sources
PARALLEL_LANGUAGE_SOURCES = {
    'opus/OpenSubtitles2018': PARALLEL_LANGUAGES,
    'opus/ParaCrawl' : [
        'de_en', 'en_es', 'en_fr', 'en_it', 'en_nl', 'en_pl', 'en_pt', 'en_sv'
    ],
    'opus/Europarl': [
        'de_en', 'en_es', 'en_fr', 'en_it', 'en_nl', 'en_pl', 'en_pt', 'en_sv'
    ],
    'opus/MultiUN' : [
        'ar_en', 'de_en', 'en_es', 'en_fr', 'en_ru', 'en_zh-x-oversimplified'
    ],
    'opus/UNPC' : [
        'ar_en', 'en_es', 'en_fr', 'en_ru', 'en_zh-x-oversimplified'
    ],
    'jesc': [
        'en_ja'
    ],
    'jparacrawl': [
        'en_ja'
    ]
}


def parallel_sources(wildcards):
    sources = []
    lang1, lang2 = sorted([wildcards.lang1, wildcards.lang2])
    pair = '{}_{}'.format(lang1, lang2)

    if pair in PARALLEL_LANGUAGE_SOURCES['opus/OpenSubtitles2018']:
        sources.append(DATA + "/parallel/sources/opus/OpenSubtitles2018.{}.txt".format(pair))
    if pair in PARALLEL_LANGUAGE_SOURCES['opus/ParaCrawl']:
        sources.append(DATA + "/parallel/sources/opus/ParaCrawl.{}.txt".format(pair))
    if pair in PARALLEL_LANGUAGE_SOURCES['opus/Europarl']:
        sources.append(DATA + "/parallel/sources/opus/Europarl.{}.txt".format(pair))
    if pair in PARALLEL_LANGUAGE_SOURCES['opus/MultiUN']:
        sources.append(DATA + "/parallel/sources/opus/MultiUN.{}.txt".format(pair))
    if pair in PARALLEL_LANGUAGE_SOURCES['opus/UNPC']:
        sources.append(DATA + "/parallel/sources/opus/UNPC.{}.txt".format(pair))
    if pair in PARALLEL_LANGUAGE_SOURCES['jesc']:
        sources.append(DATA + "/parallel/sources/jesc/{}.txt".format(pair))
    if pair in PARALLEL_LANGUAGE_SOURCES['jparacrawl']:
        sources.append(DATA + "/parallel/sources/jparacrawl/{}.txt".format(pair))
    return sources


def get_opus_version(dataset):
    # Manage the version of the OPUS datasets manually
    if dataset == 'OpenSubtitles2018':
        version = 'OPUS-OpenSubtitles/v2018'
    elif dataset == 'ParaCrawl':
        version = 'OPUS-ParaCrawl/v5'
    elif dataset == 'Europarl':
        version = 'OPUS-Europarl/v8'
    elif dataset == 'MultiUN':
        version = 'OPUS-MultiUN/v1'
    elif dataset == 'UNPC':
        version = 'OPUS-UNPC/v1.0'
    elif dataset == 'Tatoeba':
        version = 'OPUS-Tatoeba/v20190709'
    else:
        raise ValueError(f"Unknown OPUS dataset: {dataset}")
    return version


def map_opus_language(dataset, lang):
    if dataset.startswith('opus/'):
        raise ValueError("Wildcard matched incorrectly; the 'opus/' directory should not be included in the match.")
    if dataset == 'Tatoeba':
        # Tatoeba language codes are sometimes more specific than we want.
        mapping = {
            'zh-Hans': 'cmn',
            'fa': 'pes',
            'fil': 'tl',
            'sh': 'sr'
        }
    elif dataset == 'GlobalVoices':
        # GlobalVoices has three made-up language codes, plus 'sr' which we want to
        # handle as part of 'sh'.
        mapping = {
            'ja': 'jp',
            'zh-Hant': 'zht',
            'zh-Hans': 'zhs',
            'sh': 'sr'
        }
    elif dataset == 'OpenSubtitles2018':
        mapping = {
            'pt-PT': 'pt',
            'pt-BR': 'pt_br',
            'zh-Hans': 'zh_cn',
            'zh-Hant': 'zh_tw',
            'nb': 'no',
        }
    elif dataset == 'Europarl':
        mapping = {
            'pt-PT': 'pt'
        }
    elif dataset == 'ParaCrawl' or 'MultiUN' or 'UNPC':
        mapping = {}
    else:
        raise ValueError("Unknown OPUS dataset: %r" % dataset)
    return mapping.get(lang, lang)


def find_reddit_filename(wildcards):
    """
    pushshift.io's Reddit archives are compressed in different formats
    over time. Find the correct filename given the date.
    """
    yearmonth = wildcards.year + '-' + wildcards.month
    if yearmonth <= '2017-11':
        ext = '.bz2'
    elif yearmonth <= '2018-10':
        ext = '.xz'
    else:
        ext = '.zst'
    return DATA + "/downloaded/reddit/" + yearmonth + ext


def language_count_sources(lang):
    """
    Get all the sources of word counts we have in a language.
    """
    return [
        DATA + "/counts/{source}/{lang}.txt".format(source=source, lang=lang)
        for source in LANGUAGE_SOURCES[lang]
    ]


def language_text_sources(lang):
    """
    Get all the sources of tokenized text we have in a language.
    """
    return [
        DATA + "/tokenized/{source}/{lang}.txt".format(source=source, lang=lang)
        for source in LANGUAGE_SOURCES[lang]
        if source in FULL_TEXT_SOURCES
    ]


def _count_filename(source, lang):
    if '/' in source:
        return DATA + "/counts/{source}.{lang}.txt".format(source=source,
                                                         lang=lang)
    else:
        return DATA + "/counts/{source}/{lang}.txt".format(source=source,
                                                       lang=lang)


def multisource_counts_to_merge(multisource, lang):
    """
    Given a multi-source name like 'news' and a language code, find which sources
    of counts should be merged to produce it.
    """
    result = [
        _count_filename(source, lang)
        for source in MERGED_SOURCES[multisource]
        if lang in SOURCE_LANGUAGES[source]
    ]
    return result


def paracrawl_language_pair_source(lang):
    """
    Given a language code in ParaCrawl, we find the "paired" file that contains
    monolingual tokenized data from that language.

    ParaCrawl is parallel data, so its input files refer to language pairs. In
    practice, each language pair is English and a non-English language. So the
    result for most languages is that they are paired with English. English is
    paired with French, as that language pair yields the most text.

    A "paired" filename is tagged with both a language pair and a single
    language. All the text in the file is in that single language, but the
    filename also refers to the language pair that it came from. The other file
    from that language pair has corresponding lines in the same order, so you
    could 'paste' them together to get tabular parallel text, with text in one
    language and its translation in another.

    We sort the language codes to make them consistent with OPUS sources.
    """
    if lang == 'en':
        other = 'fr'
    else:
        other = 'en'

    lang1, lang2 = sorted([lang, other])
    langpair = '{}_{}'.format(lang1, lang2)

    return DATA + "/tokenized/paracrawl-paired/{langpair}.{lang}.txt".format(langpair=langpair, lang=lang)


# Top-level rules
# ===============

rule wordfreq:
    input:
        expand(DATA + "/wordfreq/small_{lang}.msgpack.gz",
               lang=SUPPORTED_LANGUAGES),
        expand(DATA + "/wordfreq/large_{lang}.msgpack.gz",
               lang=LARGE_LANGUAGES),
        DATA + "/wordfreq/jieba_zh.txt"

rule parallel:
    input:
        expand(DATA + "/parallel/training/joined/{pair}.{mode}.txt",
                pair=PARALLEL_LANGUAGE_PAIRS, mode=['train', 'valid', 'test']),
        expand(DATA + "/parallel/training/joined/tatoeba_test.{pair}.txt",
                pair=PARALLEL_LANGUAGE_PAIRS)

rule alignment:
    input:
        expand(DATA + "/parallel/training/alignment/{pair}.{mode}.txt",
                pair=PARALLEL_LANGUAGE_PAIRS, mode=['train', 'valid', 'test']),

rule frequencies:
    input:
        expand(DATA + "/freqs/{lang}.txt", lang=SUPPORTED_LANGUAGES)

rule embeddings:
    input:
        expand(DATA + "/skipgrams/{lang}.vec", lang=LARGE_LANGUAGES)

rule google_2grams:
    input:
        expand(DATA + "/downloaded/google-ngrams/2grams-en-{shard}.txt.gz",
                shard=GOOGLE_2GRAM_SHARDS)

rule google_3grams:
    input:
        expand(DATA + "/downloaded/google-ngrams/3grams-en-{shard}.txt.gz",
                shard=GOOGLE_3GRAM_SHARDS)

# Downloaders
# ===========

rule download_opus_monolingual:
    output:
        DATA + "/downloaded/opus/{dataset}.{lang}.txt.gz"
    resources:
        download=1, opusdownload=1
    priority: 0
    run:
        dataset = wildcards.dataset
        source_lang = map_opus_language(dataset, wildcards.lang)
        shell("wget 'http://opus.nlpl.eu/download.php?f={dataset}/mono/{dataset}.raw.{source_lang}.gz' -O {output}")


rule download_reddit:
    output:
        DATA + "/downloaded/reddit/{year}-{month}.{ext}"
    resources:
        download=1
    priority: 0
    shell:
        "wget 'https://files.pushshift.io/reddit/comments/RC_{wildcards.year}-{wildcards.month}.{wildcards.ext}' -O {output}"


rule download_opus_parallel:
    output:
        DATA + "/downloaded/opus/{dataset}.{lang1}_{lang2}.zip"
    resources:
        download=1, opusdownload=1
    run:
        # The filename we output will follow our language code conventions,
        # but we have to remap and reorder the language codes to get the right
        # remote filename. See the comments in `extract_opus_parallel`.
        dataset = wildcards.dataset
        lang1 = map_opus_language(dataset, wildcards.lang1)
        lang2 = map_opus_language(dataset, wildcards.lang2)
        lang1, lang2 = sorted([lang1, lang2])

        # Manage the version of the OPUS dataset manually
        version = get_opus_version(dataset)
        shell(
            "wget 'https://object.pouta.csc.fi/{version}/moses/{lang1}-{lang2}.txt.zip' -O {output}"
        )


rule download_wikipedia:
    output:
        DATA + "/downloaded/wikipedia/wikipedia_{lang}.xml.bz2"
    resources:
        download=1, wpdownload=1
    priority: 0
    run:
        source_lang = WP_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        version = WP_VERSION
        shell("wget 'https://dumps.wikimedia.org/{source_lang}wiki/{version}/{source_lang}wiki-{version}-pages-articles.xml.bz2' -O {output}")

rule download_newscrawl:
    output:
        DATA + "/downloaded/newscrawl-2014-monolingual.tar.gz"
    shell:
        "wget 'http://www.statmt.org/wmt15/training-monolingual-news-2014.tgz' -O {output}"

rule download_google_1grams:
    resources:
        download=1
    output:
        DATA + "/downloaded/google/1grams-{lang}.txt"
    run:
        source_lang = GOOGLE_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        nshards = GOOGLE_NUM_1GRAM_SHARDS[wildcards.lang]
        for shard in range(nshards):
            url = f'http://storage.googleapis.com/books/ngrams/books/20200217/{source_lang}/1-{shard:>05}-of-{nshards:>05}.gz'
            shell("curl -Lf '{url}' | gunzip -c | awk -f scripts/google-sum-columns.awk >> {output}")

rule download_google_ngrams:
    output:
        DATA + "/downloaded/google-ngrams/{n}grams-{lang}-{shard}.txt.gz"
    run:
        source_lang = GOOGLE_LANGUAGE_MAP.get(wildcards.lang, wildcards.lang)
        shard = wildcards.shard
        n = wildcards.n
        # Do a bit of pre-processing as we download
        shell("curl -Lf 'http://storage.googleapis.com/books/ngrams/books/googlebooks-{source_lang}-fiction-all-{n}gram-20120701-{shard}.gz' | zcat | cut -f 1,3 | gzip -c > {output}")

rule download_amazon_snap:
    output:
        DATA + "/downloaded/amazon/{category}.json.gz"
    shell:
        "wget 'http://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_{wildcards.category}_5.json.gz' -O {output}"

rule download_amazon_acl10:
    output:
        DATA + "/downloaded/amazon/cls-acl10-unprocessed.tar.gz"
    shell:
        "wget 'http://www.uni-weimar.de/medien/webis/corpora/corpus-webis-cls-10/cls-acl10-unprocessed.tar.gz' -O {output}"

rule download_paracrawl:
    output:
        DATA + "/downloaded/paracrawl/{lang1}_{lang2}.tmx.gz"
    run:
        # Put the language codes in ParaCrawl order, with English first
        if wildcards.lang1 == 'en':
            otherlang = wildcards.lang2
        elif wildcards.lang2 == 'en':
            otherlang = wildcards.lang1
        else:
            raise ValueError("One language in a ParaCrawl pair must be English")

        shell("wget 'https://s3.amazonaws.com/web-language-models/paracrawl/release1.2/paracrawl-release1.2.en-{otherlang}.withstats.filtered-bicleaner.tmx.gz' -O {output}")

rule download_jesc:
    output:
        DATA + "/downloaded/jesc/raw.tar.gz"
    shell:
        "curl -Lf 'https://nlp.stanford.edu/projects/jesc/data/raw.tar.gz' -o {output}"


rule download_jparacrawl:
    output:
        DATA + "/downloaded/jparacrawl/en-ja.tar.gz"
    shell:
        "wget 'http://www.kecl.ntt.co.jp/icl/lirg/jparacrawl/release/2.0/bitext/en-ja.tar.gz' -O {output}"


# Handling downloaded data
# ========================
rule extract_opus_parallel:
    input:
        DATA + "/downloaded/opus/{dataset}.{lang1}_{lang2}.zip"
    output:
        temp(DATA + "/extracted/opus/{dataset}.{lang1}_{lang2}.{lang1}"),
        temp(DATA + "/extracted/opus/{dataset}.{lang1}_{lang2}.{lang2}")
    run:
        # The contents of the zip file have OPUS language codes joined by
        # hyphens.  We need to rename them to our BCP 47 language codes joined
        # by underscores.
        #
        # Handling an edge case with inconsistent language codes here requires
        # some careful explanation.
        #
        # 'lang1' and 'lang2' are our language codes, as requested by the
        # output rule. We use the same language codes to name the input file,
        # because when we download the OPUS file (in `download_opus_parallel`),
        # we can give it any name we want. The trickier part, however, is that
        # the file we download is a zip file containing specified filenames,
        # using the language codes that are idiosyncratic to each OPUS dataset,
        # so we need to rename those files to produce the right output.
        #
        # 'code1' and 'code2' are 'lang1' and 'lang2' mapped into OPUS codes.
        # We then sort them, so that 'codeA' is the first one alphabetically,
        # and 'codeB' is the second one, because they will be given in that
        # order in the filename. We need all these variables to determine which
        # files to move where.
        #
        # Oh, and OPUS uses hyphens and underscores backwards from how we use
        # them.
        #
        # For example, when we convert our language pair "en_zh-Hans" to the
        # codes OPUS uses for Tatoeba, "zh-Hans" is replaced by "cmn". But
        # the OPUS code isn't "en_cmn", it's "cmn_en", because of alphabetical
        # order.

        dataset = wildcards.dataset
        if dataset == 'OpenSubtitles2018':
            # OPUS renamed the contents of their zip files from
            # 'OpenSubtitles2018' to 'OpenSubtitles'.
            zip_dataset = 'OpenSubtitles'
        else:
            zip_dataset = dataset
        code1 = map_opus_language(dataset, wildcards.lang1)
        code2 = map_opus_language(dataset, wildcards.lang2)
        codeA, codeB = sorted([code1, code2])
        zip_output1 = DATA + "/extracted/opus/{zip_dataset}.{codeA}-{codeB}.{code1}".format(
            code1=code1, code2=code2, codeA=codeA, codeB=codeB, zip_dataset=zip_dataset
        )
        zip_output2 = DATA + "/extracted/opus/{zip_dataset}.{codeA}-{codeB}.{code2}".format(
            code1=code1, code2=code2, codeA=codeA, codeB=codeB, zip_dataset=zip_dataset
        )
        output1, output2 = output
        shell("unzip -o -d '{DATA}/extracted/opus/' {input} && mv {"
              "zip_output1} {output1} && mv {zip_output2} {output2} && touch {output}")


rule extract_jesc:
    input:
        DATA + "/downloaded/jesc/raw.tar.gz"
    output:
        temp(DATA + "/extracted/jesc/raw/raw")
    shell:
        "tar xf {input} -C {DATA}/extracted/jesc && touch {output}"


rule extract_jparacrawl:
    input:
        DATA + "/downloaded/jparacrawl/en-ja.tar.gz"
    output:
        temp(DATA + "/extracted/jparacrawl/en-ja/en-ja.bicleaner05.txt")
    shell:
        "tar xf {input} -C {DATA}/extracted/jparacrawl && touch {output}"


rule extract_newscrawl:
    input:
        DATA + "/downloaded/newscrawl-2014-monolingual.tar.gz"
    output:
        expand(temp(DATA + "/extracted/newscrawl/training-monolingual-news" \
                         "-2014/news.2014.{lang}.shuffled"), lang=SOURCE_LANGUAGES['newscrawl'])
    shell:
        "tar xf {input} -C {DATA}/extracted/newscrawl && touch " \
        "{DATA}/extracted/newscrawl/training-monolingual-news-2014/*"

rule gzip_newscrawl:
    input:
        DATA + "/extracted/newscrawl/training-monolingual-news-2014/news" \
               ".2014.{lang}.shuffled"
    output:
        DATA + "/extracted/newscrawl/training-monolingual-news-2014/news" \
               ".2014.{lang}.shuffled.gz"
    shell:
        "gzip -c {input} > {output}"

rule extract_amazon_acl10:
    input:
        DATA + "/downloaded/amazon/cls-acl10-unprocessed.tar.gz"
    output:
        expand(temp(DATA + "/extracted/amazon-acl10/cls-acl10-unprocessed/{" \
                      "lang}/{dataset}.review"),
               lang=AMAZON_ACL_CODES,
               dataset=AMAZON_ACL_DATASETS)
    shell:
        "tar xf {input} -C {DATA}/extracted/amazon-acl10 && touch {output}"

rule extract_google_1grams:
    input:
        DATA + "/downloaded/google/1grams-{lang}.txt"
    output:
        DATA + "/messy-counts/google/{lang}.txt"
    shell:
        # Lowercase the terms, remove part-of-speech tags such as _NOUN, and
        # run the result through the 'countmerge' utility
        r"LANG=C sort {input} | awk -f scripts/countmerge.awk > {output}"

rule extract_reddit:
    input: find_reddit_filename
    output:
        DATA + "/extracted/reddit/{year}-{month}.txt.gz"
    shell:
        "xc preprocess-reddit {input} | gzip -c > {output}"

rule extract_amazon:
    input:
        DATA + "/downloaded/amazon/{category}.json.gz"
    output:
        temp(DATA + "/extracted/amazon-snap/{category}.csv")
    shell:
        r"""zcat {input} | jq -r -c '"label__\(.["overall"] | tostring)\t\(.["summary"])\t\(.["reviewText"])"' > {output}"""

rule extract_voa_fa:
    input:
        DATA + "/extra/voa_fa_2003-2008_orig.txt"
    output:
        temp(DATA + "/extracted/voa/fa.txt")
    shell:
        "sed -e 's/^# Headline: //' -e 's/^#.*//' {input} > {output}"


# Monolingual corpus
# ==================
# You would think we can parametrize these by language and write the rule just
# once. But we have different sets of sources available for each language, I'd
# rather not write the logic for that, and some languages need special handling
# (for example, English Reddit requires 10% sub-sampling).

rule monolingual_corpus_en:
    input:
        DATA + "/extracted/newscrawl/training-monolingual-news-2014/news.2014.en.shuffled.gz",
        DATA + "/extracted/wikipedia/en.txt.gz",
        DATA + "/downloaded/opus/OpenSubtitles2018.en.txt.gz",
        DATA + "/downloaded/opus/Europarl.en.txt.gz",
        DATA + "/downloaded/opus/GlobalVoices.en.txt.gz",
        expand(DATA + "/extracted/twitter1/twitter-{year}.txt.gz", year=[2014, 2015, 2016, 2017, 2018]) if INCLUDE_TWITTER else [],
        expand(DATA + "/extracted/reddit/{shard}.txt.gz", shard=SAMPLED_REDDIT_SHARDS)
    output:
        DATA + "/monolingual/en.txt.gz"
    shell:
        "zcat {input} | awk -f scripts/language-tag-filter.awk -v lang=en | scripts/imperfect-shuffle-gz.sh {output} monolingual_en"


# Get a 1% sample of the corpus, for training a process such as SentencePiece
# that requires diverse, representative data, but not _all_ the data.
#
# For the benefit of SentencePiece, also wrap the lines to a maximum length
# of 1000 characters.
rule monolingual_subsample_en:
    input:
        DATA + "/monolingual/en.txt.gz"
    output:
        DATA + "/monolingual/en.sample.txt"
    shell:
        "zcat {input} | fold -w 1000 -s | awk 'NR % 100 == 0' > {output}"


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
        DATA + "/source-lists/leeds/internet-{lang}-forms.num"
    output:
        DATA + "/messy-counts/leeds/{lang}.txt"
    shell:
        "sed -rn -e 's/([0-9]+) ([0-9]+).([0-9][0-9]) (.*)/\\4\t\\2\\3/p' {input} | grep -v 'EOS\t' > {output}"

# The Mokk Hungarian Web corpus comes from scraping all known .hu Web sites and
# filtering the results for whether they seemed to actually be Hungarian. The
# list contains different counts at different levels of filtering; we choose
# the second most permissive level, which is in the 3rd tab-separated field.

rule transform_mokk:
    input:
        DATA + "/source-lists/mokk/web2.2-freq-sorted.txt"
    output:
        DATA + "/messy-counts/mokk/hu.txt"
    shell:
        "iconv -f iso-8859-2 -t utf-8 {input} | cut -f 1,3 > {output}"

# SUBTLEX is different in each instance.
# The main issue with German is that it's mostly (but not entirely) in
# double-UTF-8.
rule transform_subtlex_de:
    input:
        DATA + "/source-lists/subtlex/subtlex.de.txt"
    output:
        DATA + "/messy-counts/subtlex/de.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,3 | ftfy > {output}"

rule transform_subtlex_en:
    input:
        DATA + "/source-lists/subtlex/subtlex.en-{region}.txt"
    output:
        DATA + "/messy-counts/subtlex/en-{region}.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,2 > {output}"

rule transform_subtlex_nl:
    input:
        DATA + "/source-lists/subtlex/subtlex.nl.txt"
    output:
        DATA + "/messy-counts/subtlex/nl.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,2 > {output}"

rule transform_subtlex_pl:
    input:
        DATA + "/source-lists/subtlex/subtlex.pl.txt"
    output:
        DATA + "/messy-counts/subtlex/pl.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,5 > {output}"

rule transform_subtlex_zh:
    input:
        DATA + "/source-lists/subtlex/subtlex.zh.txt"
    output:
        DATA + "/messy-counts/subtlex/zh-Hans.txt"
    shell:
        "tail -n +2 {input} | cut -f 1,5 > {output}"

rule transform_jieba:
    input:
        DATA + "/source-lists/jieba/dict.txt.big"
    output:
        DATA + "/messy-counts/jieba/zh.txt"
    shell:
        "cut -d ' ' -f 1,2 {input} | tr ' ' '\t' | xc simplify-chinese - {output}"

rule transform_2grams:
    input:
        DATA + "/downloaded/google-ngrams/2grams-{lang}-{prefix}.txt.gz"
    output:
        DATA + "/messy-counts/google-ngrams/2grams-{lang}-{prefix}.txt"
    shell:
        r"zcat {input} | sed -re 's/_[A-Z.]*//g' | tr A-Z a-z | awk -f scripts/countmerge.awk > {output}"

rule transform_3grams:
    input:
        DATA + "/downloaded/google-ngrams/3grams-{lang}-{prefix}.txt.gz"
    output:
        DATA + "/messy-counts/google-ngrams/3grams-{lang}-{prefix}.txt"
    shell:
        r"zcat {input} | sed -re 's/_[A-Z.]*//g' | tr A-Z a-z | awk -f scripts/countmerge.awk > {output}"

rule concat_2grams:
    input:
        expand(DATA + "/messy-counts/google-ngrams/2grams-en-{prefix}.txt",
                prefix=GOOGLE_2GRAM_SHARDS)
    output:
        DATA + "/messy-counts/google-ngrams/2grams-combined-en.txt.gz"
    shell:
        "grep -Eh '[0-9]{{3,}}$' {input} | LANG=C sort | awk -f scripts/countmerge.awk | gzip -c > {output}"

rule concat_3grams:
    input:
        expand(DATA + "/messy-counts/google-ngrams/3grams-en-{prefix}.txt",
                prefix=GOOGLE_3GRAM_SHARDS)
    output:
        DATA + "/messy-counts/google-ngrams/3grams-combined-en.txt.gz"
    shell:
        "grep -Eh '[0-9]{{3,}}$' {input} | LANG=C sort | awk -f scripts/countmerge.awk | gzip -c > {output}"

rule transform_paracrawl:
    # To save computation time, we use fast command-line tools to do as much
    # processing as possible, particularly for tasks such as streaming XML
    # processing. Python's SAX would do this, but it's slow and its API is
    # painful. So we use 'xml2' instead.
    #
    # xml2 is a command-line XML processor that outputs a stream of lines
    # representing completed elements and their attributes. The output is
    # suited for processing with further command-line tools; in this case,
    # it seems that 'awk' is the best one for the job. This awk script
    # assembles the stream of XML elements into language-tagged lines.
    input:
        DATA + "/downloaded/paracrawl/{lang1}_{lang2}.tmx.gz"
    output:
        temp(DATA + "/extracted/paracrawl/pairs/{lang1}_{lang2}.txt")
    shell:
        "zcat {input} | xml2 | awk -f ./scripts/tmx-language-tagger.awk > {output}"


rule select_paracrawl_language:
    # The output of tmx-language-tagger.awk is tab-separated lines of
    # a language code and text in that language, which occur in parallel
    # pairs from two different languages.
    #
    # This rule selects just the text from the lines in one language. (We'll
    # track the language in the filename.)
    input:
        DATA + "/extracted/paracrawl/pairs/{langpair}.txt"
    output:
        temp(DATA + "/extracted/paracrawl/{langpair}.{lang}.txt")
    shell:
        "grep '^{wildcards.lang}\\s' {input} | cut -f 2 > {output}"


# Tokenizing
# ==========

rule extract_wikipedia:
    input:
        DATA + "/downloaded/wikipedia/wikipedia_{lang}.xml.bz2"
    output:
        DATA + "/extracted/wikipedia/{lang}.txt.gz"
    shell:
        "bunzip2 -c {input} | wiki2text | gzip -c > {output}"

rule tokenize_wikipedia:
    input:
        DATA + "/extracted/wikipedia/{lang}.txt.gz"
    output:
        DATA + "/tokenized/wikipedia/{lang}.txt"
    shell:
        "zcat {input} | xc tokenize -p -l {wildcards.lang} - {output}"

rule tokenize_amazon:
    input:
        expand(DATA + "/extracted/amazon-snap/{category}.csv",
                category=AMAZON_CATEGORIES)
    output:
        expand(DATA + "/tokenized/amazon-snap/en.txt")
    shell:
        "sed -e 's/\t/ ¶ /g' {input} | xc tokenize -p -l en | sed -e 's/label__/__label__/' > {output}"

rule tokenize_opus:
    input:
        DATA + "/downloaded/opus/{dataset}.{lang}.txt.gz"
    output:
        DATA + "/tokenized/opus/{dataset}.{lang}.txt"
    shell:
        # Remove country codes and fix mojibake
        "gunzip -c {input} | sed -e 's/([A-Z][A-Z]\+)//g' | ftfy | xc tokenize -p -l {wildcards.lang} - {output}"

rule tokenize_newscrawl:
    input:
        DATA + "/extracted/newscrawl/training-monolingual-news-2014/news" \
               ".2014.{lang}.shuffled.gz"
    output:
        DATA + "/tokenized/newscrawl/{lang}.txt"
    shell:
        "zcat {input} | xc tokenize -c -p -l {wildcards.lang} - {output}"

rule tokenize_parallel_opus:
    input:
        DATA + "/extracted/opus/{dataset}.{langpair}.{lang}"
    output:
        DATA + "/tokenized/opus/{dataset}.{langpair}.{lang}.txt"
    shell:
        "xc tokenize -f -p -l {wildcards.lang} {input} {output}"

rule tokenize_paracrawl:
    # Tokenize the text from Paracrawl, in one language at a time, but keeping
    # track of the language pair they originated from.
    input:
        DATA + "/extracted/paracrawl/{langpair}.{lang}.txt"
    output:
        DATA + "/tokenized/paracrawl-paired/{langpair}.{lang}.txt"
    shell:
        "xc tokenize -f -p -l {wildcards.lang} {input} {output}"

rule tokenize_paracrawl_monolingual:
    # We've already tokenized the text of Paracrawl in the rule above.
    # For the benefit of builds that don't care about parallel text, we
    # need to find the one 'correct' file containing monolingual text for
    # each language.
    #
    # Those files already exist; we just need them to exist under a
    # filename where we only need to know the language code to find them.
    # So we make a temporary copy of the file under that name.
    input:
        lambda wildcards: paracrawl_language_pair_source(wildcards.lang)
    output:
        temp(DATA + "/tokenized/paracrawl/{lang}.txt")
    shell:
        "cp {input} {output}"

rule tokenize_reddit:
    input:
        DATA + "/extracted/reddit/{date}.txt.gz"
    output:
        expand(DATA + "/tokenized/reddit/{{date}}/{lang}.txt",
               lang=SOURCE_LANGUAGES['reddit/merged'])
    params:
        languages = ','.join(SOURCE_LANGUAGES['reddit/merged'])
    shell:
        "zcat {input} | xc tokenize-by-language -l {params.languages} - " \
        "{DATA}/tokenized/reddit/{wildcards.date}"

rule extract_twitter:
    input:
        DATA + "/raw/twitter1/twitter-{year}.txt.gz"
    output:
        DATA + "/extracted/twitter1/twitter-{year}.txt.gz"
    shell:
        "zcat {input} | xc preprocess-twitter | gzip -c > {output}"


rule extract_twitter_v2:
    input:
        expand(DATA + "/raw/twitter2/{year}/tweets.{{lang}}.jsonl", year=TWITTER_V2_YEARS)
    output:
        DATA + "/extracted/twitter2/{lang}.txt.gz"
    shell:
        "jq -r '.text' {input} | gzip -c > {output}"


rule tokenize_twitter:
    input:
        DATA + "/extracted/twitter1/twitter-2014.txt.gz",
        DATA + "/extracted/twitter1/twitter-2015.txt.gz",
        DATA + "/extracted/twitter1/twitter-2016.txt.gz",
        DATA + "/extracted/twitter1/twitter-2017.txt.gz",
        DATA + "/extracted/twitter1/twitter-2018.txt.gz"
    output:
        expand(DATA + "/tokenized/twitter1/{lang}.txt", lang=SOURCE_LANGUAGES.get('twitter1', []))
    params:
        languages = ','.join(SOURCE_LANGUAGES.get('twitter1', []))
    shell:
        "zcat {input} | xc tokenize-by-language -l {params.languages} - " \
        "{DATA}/tokenized/twitter1"


rule tokenize_twitter_v2_balkans:
    input:
        DATA + "/extracted/twitter2/bs.txt.gz",
        DATA + "/extracted/twitter2/hr.txt.gz",
        DATA + "/extracted/twitter2/sr.txt.gz"
    output:
        DATA + "/tokenized/twitter2/sh.txt"
    shell:
        "zcat {input} | xc tokenize -l sh - {output}"

rule tokenize_twitter_v2:
    input:
        DATA + "/extracted/twitter2/{lang}.txt.gz"
    output:
        DATA + "/tokenized/twitter2/{lang}.txt"
    shell:
        "zcat {input} | xc tokenize -c -l {wildcards.lang} - {output}"

rule tokenize_voa:
    input:
        DATA + "/extracted/voa/{lang}.txt"
    output:
        DATA + "/tokenized/voa/{lang}.txt"
    shell:
        "xc tokenize -p -l {wildcards.lang} - {output}"


# Handling parallel text
# ======================

# Merge zh-Hans and zh-Hant data obtained from OpenSubtitles and simplify them as
# zh-x-oversimplified
rule merge_and_simplify_opensubtitles_zh:
     input:
         DATA + "/extracted/opus/OpenSubtitles2018.en_zh-Hans.zh-Hans",
         DATA + "/extracted/opus/OpenSubtitles2018.en_zh-Hant.zh-Hant",
         DATA + "/extracted/opus/OpenSubtitles2018.en_zh-Hans.en",
         DATA + "/extracted/opus/OpenSubtitles2018.en_zh-Hant.en"
     output:
         temp(DATA + "/extracted/opus/OpenSubtitles2018.en_zh-x-oversimplified.zh-x-oversimplified"),
         temp(DATA + "/extracted/opus/OpenSubtitles2018.en_zh-x-oversimplified.en")
     run:
         input_Hans, input_Hant, input_en1, input_en2 = input
         output_zh, output_en = output
         shell(
         "cat {input_Hans} {input_Hant} | xc simplify-chinese > {output_zh} && "
         "cat {input_en1} {input_en2} > {output_en}"
         )


rule simplify_multi_un_zh:
     input:
         DATA + "/extracted/opus/MultiUN.en_zh.zh",
         DATA + "/extracted/opus/MultiUN.en_zh.en"
     output:
         temp(DATA + "/extracted/opus/MultiUN.en_zh-x-oversimplified.zh-x-oversimplified"),
         temp(DATA + "/extracted/opus/MultiUN.en_zh-x-oversimplified.en")
     run:
         input_zh, input_en = input
         output_zh, output_en = output
         shell(
         "xc simplify-chinese {input_zh} {output_zh} && "
         "cp {input_en} {output_en}"
         )


rule simplify_unpc_zh:
     input:
         DATA + "/extracted/opus/UNPC.en_zh.zh",
         DATA + "/extracted/opus/UNPC.en_zh.en"
     output:
         temp(DATA + "/extracted/opus/UNPC.en_zh-x-oversimplified.zh-x-oversimplified"),
         temp(DATA + "/extracted/opus/UNPC.en_zh-x-oversimplified.en")
     run:
         input_zh, input_en = input
         output_zh, output_en = output
         shell(
         "xc simplify-chinese {input_zh} {output_zh} && "
         "cp {input_en} {output_en}"
         )

rule simplify_tatoeba_zh:
     input:
         DATA + "/extracted/opus/Tatoeba.en_zh-Hans.zh-Hans",
         DATA + "/extracted/opus/Tatoeba.en_zh-Hans.en"
     output:
         temp(DATA + "/extracted/opus/Tatoeba.en_zh-x-oversimplified.zh-x-oversimplified"),
         temp(DATA + "/extracted/opus/Tatoeba.en_zh-x-oversimplified.en")
     run:
         input_Hans, input_en = input
         output_zh, output_en = output
         shell(
         "xc simplify-chinese {input_Hans} {output_zh} && "
         "cp {input_en} {output_en}"
         )


rule parallel_opus:
    # Join monolingual files from OPUS into a parallel text file.
    input:
        DATA + "/extracted/opus/{dataset}.{lang1}_{lang2}.{lang1}",
        DATA + "/extracted/opus/{dataset}.{lang1}_{lang2}.{lang2}"

    output:
        DATA + "/parallel/sources/opus/{dataset}.{lang1}_{lang2}.txt"
    shell:
        # OpenSubtitles text may have come out in a form of Chinese mojibake
        # where many characters are mapped to the private use area.
        #
        # Unfortunately, we can't grep those out using a Unicode-aware range.
        # Ranges depend on Unicode collation, and the collation of private-use
        # characters is undefined.
        #
        # Instead, we read the file as UTF-8 bytes with LANG=C, and grep to
        # exclude byte 0xEE (which we express using the Bash-ism $'' to
        # evaluate an escape sequence), the UTF-8 byte that begins all
        # private-use codepoints from U+E000 to U+EFFF. That's not all the
        # private-use codepoints, but it covers most of the OpenSubtitles
        # mojibake.
        "paste {input} | LANG=C grep -v $'\xee' > {output}"


rule parallel_paracrawl:
    # Join monolingual files from ParaCrawl into a parallel text file.
    input:
        DATA + "/extracted/paracrawl/{lang1}_{lang2}.{lang1}.txt",
        DATA + "/extracted/paracrawl/{lang1}_{lang2}.{lang2}.txt"

    output:
        DATA + "/parallel/paracrawl/{lang1}_{lang2}.txt"
    shell:
        "paste {input} > {output}"


rule parallel_jesc:
    input:
        DATA + "/extracted/jesc/raw/raw"
    output:
        DATA + "/parallel/sources/jesc/en_ja.txt"
    shell:
        "cp {input} {output}"


rule parallel_jparacrawl:
    input:
        DATA + "/extracted/jparacrawl/en-ja/en-ja.bicleaner05.txt"
    output:
        DATA + "/parallel/sources/jparacrawl/en_ja.txt"
    shell:
         # en-ja.bicleaner05.txt contains tab-separated domain name, score, English
         # text, and Japanese text
        "cut -f 3,4 {input} > {output}"


rule shuffle_parallel:
    input: parallel_sources
    output:
        DATA + "/parallel/shuffled/{lang1}_{lang2}.txt"
    shell:
        "cat {input} | scripts/imperfect-shuffle.sh {output} parallel_{wildcards.lang1}_{wildcards.lang2}"


rule cleanup_parallel:
    input:
        DATA + "/parallel/shuffled/{lang1}_{lang2}.txt"
    output:
        DATA + "/parallel/shuffled-clean/{lang1}_{lang2}.txt"
    shell:
        "xc cleanup-parallel {input} {output} {wildcards.lang1} {wildcards.lang2}"


rule separate_parallel:
    input:
        DATA + "/parallel/shuffled-clean/{lang1}_{lang2}.txt"
    output:
        temp(DATA + "/parallel/shuffled-split/{lang1}_{lang2}.{lang1}.all.txt"),
        temp(DATA + "/parallel/shuffled-split/{lang1}_{lang2}.{lang2}.all.txt")
    run:
        out1, out2 = output
        shell("cut -f 1 {input} > {out1} && cut -f 2 {input} > {out2}")


# Split files into train, valid, and test sets; 10000 lines for valid and test set each
# and rest is kept for the train set.
rule split_train_valid_test:
    input:
        DATA + "/parallel/shuffled-split/{pair}.{lang}.all.txt"
    output:
        DATA + "/parallel/shuffled-split/{pair}.{lang}.train.txt",
        DATA + "/parallel/shuffled-split/{pair}.{lang}.valid.txt",
        DATA + "/parallel/shuffled-split/{pair}.{lang}.test.txt"
    run:
        train_file, valid_file, test_file = output
        shell(
            "sed -n '1,10000p' {input} > {test_file} && "
            "sed -n '10001,20000p' {input} > {valid_file} && "
            "tail -n +20001 {input} > {train_file}"
        )

# Train SentencePiece model on the train set and get the vocabulary (one piece per line).
# Maximum size of sentences the trainer loads, by randomly sampling, is 1M.
rule train_sentencepiece:
    input:
        "data/parallel/shuffled-split/{pair}.{lang}.train.txt",
    output:
        "data/parallel/training/sp/{pair}.{lang}.model",
        "data/parallel/training/sp/{pair}.{lang}.nmt.vocab"
    resources:
        sp_trainer=1
    run:
        model_file, nmt_vocab_file = output
        shell(
            "xc train-sp {input} data/parallel/training/sp/{wildcards.pair}.{wildcards.lang} {wildcards.lang} && "
            "xc get-vocab-sp {nmt_vocab_file} {model_file}"
        )


# Encode raw train, valid, and test set into sentence pieces.
rule apply_sentencepiece:
    input:
        DATA + "/parallel/shuffled-split/{pair}.{lang}.{mode}.txt",
        DATA + "/parallel/training/sp/{pair}.{lang}.model"
    output:
        temp(DATA + "/tmp/paired/{pair}.{lang}.{mode}.txt")
    run:
        in_file, model_file = input
        shell(
            "xc encode-with-sp {in_file} {output} {model_file}"
        )


rule apply_sentencepiece_tatoeba:
    input:
        DATA + "/extracted/opus/Tatoeba.{pair}.{lang}",
        DATA + "/parallel/training/sp/{pair}.{lang}.model"
    output:
        temp(DATA + "/tmp/paired/tatoeba_test.{pair}.{lang}.txt")
    run:
        in_file, model_file = input
        shell(
            "xc encode-with-sp {in_file} {output} {model_file}"
        )

# Input to fast_align must be tokenized and aligned into parallel sentences. Each line
# is a source and target separated by a triple pipe symbol with leading and trailing
# white space ( ||| ). To generate these, we paste two files together and replace '\t'
# with this symbol.
# Tokenization can create empty source or target side- remove those lines so that
# fast_align would not throw an error.
# Finally, we make paired files from the joined file.
rule get_training_data:
    input:
        DATA + "/tmp/paired/{lang1}_{lang2}.{lang1}.{mode}.txt",
        DATA + "/tmp/paired/{lang1}_{lang2}.{lang2}.{mode}.txt"
    output:
        DATA + "/parallel/training/joined/{lang1}_{lang2}.{mode}.txt",
        DATA + "/parallel/training/joined/{lang2}_{lang1}.{mode}.txt",
        DATA + "/parallel/training/paired/{lang1}_{lang2}.{lang1}.{mode}.txt",
        DATA + "/parallel/training/paired/{lang1}_{lang2}.{lang2}.{mode}.txt"

    run:
        input1, input2 = input
        joined1, joined2, paired1, paired2 = output
        shell(
            "paste -d '\t' {input1} {input2} | sed 's/\t/ ||| /g' > {joined1} && "
            "sed -i -e '/^ |||/d' -e '/||| $/d' {joined1} && "
            "paste -d '\t' {input2} {input1} | sed 's/\t/ ||| /g' > {joined2} && "
            "sed -i -e '/^ |||/d' -e '/||| $/d' {joined2} && "
            "sed 's/ ||| /\t/g' {joined1} | cut -d '\t' -f 1 > {paired1} && "
            "sed 's/ ||| /\t/g' {joined1} | cut -d '\t' -f 2 > {paired2}"
        )


rule get_tatoeba_data:
    input:
        DATA + "/tmp/paired/tatoeba_test.{lang1}_{lang2}.{lang1}.txt",
        DATA + "/tmp/paired/tatoeba_test.{lang1}_{lang2}.{lang2}.txt"
    output:
        DATA + "/parallel/training/joined/tatoeba_test.{lang1}_{lang2}.txt",
        DATA + "/parallel/training/joined/tatoeba_test.{lang2}_{lang1}.txt",
        DATA + "/parallel/training/paired/tatoeba_test.{lang1}_{lang2}.{lang1}.txt",
        DATA + "/parallel/training/paired/tatoeba_test.{lang1}_{lang2}.{lang2}.txt"

    run:
        input1, input2 = input
        joined1, joined2, paired1, paired2 = output
        shell(
            "paste -d '\t' {input1} {input2} | sed 's/\t/ ||| /g' > {joined1} && "
            "sed -i -e '/^ |||/d' -e '/||| $/d' {joined1} && "
            "paste -d '\t' {input2} {input1} | sed 's/\t/ ||| /g' > {joined2} && "
            "sed -i -e '/^ |||/d' -e '/||| $/d' {joined2} && "
            "sed 's/ ||| /\t/g' {joined1} | cut -d '\t' -f 1 > {paired1} && "
            "sed 's/ ||| /\t/g' {joined1} | cut -d '\t' -f 2 > {paired2}"
        )

# fast_align generates asymmetric alignments (by default, it treats the left language in
# the parallel corpus as primary language being modeled).
# Options used with fast_align:
# -i: Input parallel corpus
# -d: (strongly recommended) Favor alignment points close to the monotonic diagonal
# -o: (strongly recommended) Optimize how close to the diagonal alignment points should be
# -v: (strongly recommended) Use Dirichlet prior on lexical translation distributions

# Sometimes fast_aline outputs an empty line in the alignment file. We fill those with
# '0-0' so that OpenNMT-py's pre-processing would not throw an error.
rule get_alignment:
    input:
        DATA + "/parallel/training/joined/{lang1}_{lang2}.{mode}.txt",
        DATA + "/parallel/training/joined/{lang2}_{lang1}.{mode}.txt"
    output:
        DATA + "/parallel/training/alignment/{lang1}_{lang2}.{mode}.txt",
        DATA + "/parallel/training/alignment/{lang2}_{lang1}.{mode}.txt"
    resources:
        alignment=1
    run:
        input1, input2 = input
        outfile1, outfile2 = output
        shell(
            "./fast_align -i {input1} -d -o -v > {outfile1} && "
            "sed -i 's/^$/0-0/' {outfile1} && "
            "./fast_align -i {input2} -d -o -v > {outfile2} && "
            "sed -i 's/^$/0-0/' {outfile2}"
        )


rule learn_sentencepiece:
    input:
        DATA + "/monolingual/{lang}.sample.txt"
    output:
        DATA + "/sentencepiece/{lang}.model",
        DATA + "/sentencepiece/{lang}.vocab"
    shell:
        # spm_train is the command to train a SentencePiece model.
        # Its command-line options are poorly and inaccurately documented,
        # so I will explain them here.
        "spm_train "
        # The filename of input text that the model will be trained on:
        "--input {DATA}/monolingual/{wildcards.lang}.sample.txt "
        # Contrary to the documentation, the format can just be plain text separated by newlines:
        "--input_format text "
        # Add '.model' and '.vocab' to this to get the output filenames:
        "--model_prefix {DATA}/sentencepiece/{wildcards.lang} "
        # Case-fold, apply NFKC, and apply a couple other substitutions that
        # machine translation people have found useful:
        "--normalization_rule_name nmt_nfkc_cf"


# Counting tokens
# ===============
rule count_tokens:
    input:
        DATA + "/tokenized/{source}/{lang}.txt"
    output:
        DATA + "/messy-counts/{source}/{lang}.txt"
    shell:
        "xc count {input} {output}"

# Merging frequencies
rule merge_freqs:
    input:
        lambda wildcards: language_count_sources(wildcards.lang)
    output:
        DATA + "/freqs/{lang}.txt"
    shell:
        "xc merge-freqs {input} {output}"

# Counts to frequencies without merging
rule count_to_freqs:
    input:
        DATA + "/counts/{source}/{lang}.txt"
    output:
        DATA + "/freqs/{source}/{lang}.txt"
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
        expand(DATA + "/tokenized/opus/OpenSubtitles2018.{lang}.txt",
                    lang=['bs', 'hr', 'sr'])
    output:
        DATA + "/tokenized/opus/OpenSubtitles2018.sh.txt"
    shell:
        "grep -vh '[А-Яа-я]' {input} > {output}"

rule recount_messy_tokens:
    input:
        DATA + "/messy-counts/{source}/{lang}.txt"
    output:
        DATA + "/counts/{source}/{lang}.txt"
    shell:
        "xc recount {input} {output} -l {wildcards.lang}"

rule merge_reddit:
    input:
        expand(DATA + "/counts/reddit/{date}/{{lang}}.txt", date=REDDIT_SHARDS)
    output:
        DATA + "/counts/reddit/merged/{lang}.txt"
    shell:
        "cat {input} | xc recount - {output} -l {wildcards.lang}"

rule merge_subtlex_en:
    input:
        DATA + "/counts/subtlex/en-GB.txt",
        DATA + "/counts/subtlex/en-US.txt",
    output:
        DATA + "/counts/subtlex/en.txt"
    shell:
        "cat {input} | xc recount - {output} -l en"

rule merge_opensubtitles_pt:
    input:
        DATA + "/tokenized/opus/OpenSubtitles2018.pt-BR.txt",
        DATA + "/tokenized/opus/OpenSubtitles2018.pt-PT.txt",
    output:
        DATA + "/tokenized/opus/OpenSubtitles2018.pt.txt"
    shell:
        "cat {input} > {output}"

rule merge_opensubtitles_zh:
    input:
        DATA + "/tokenized/opus/OpenSubtitles2018.zh-Hans.txt",
        DATA + "/tokenized/opus/OpenSubtitles2018.zh-Hant.txt",
    output:
        DATA + "/tokenized/opus/OpenSubtitles2018.zh.txt"
    shell:
        "cat {input} | xc simplify-chinese - {output}"

rule merge_globalvoices_zh:
    input:
        DATA + "/tokenized/opus/GlobalVoices.zh-Hans.txt",
        DATA + "/tokenized/opus/GlobalVoices.zh-Hant.txt",
    output:
        DATA + "/tokenized/opus/GlobalVoices.zh.txt"
    shell:
        "cat {input} | xc simplify-chinese > {output}"

rule copy_google_zh:
    input:
        DATA + "/counts/google/zh-Hans.txt"
    output:
        DATA + "/counts/google/zh.txt"
    shell:
        "xc simplify-chinese {input} {output}"

rule copy_tatoeba_zh:
    input:
        DATA + "/tokenized/tatoeba/zh-Hans.txt"
    output:
        DATA + "/tokenized/tatoeba/zh.txt"
    shell:
        "cp {input} {output}"

rule copy_subtlex_zh:
    input:
        DATA + "/counts/subtlex/zh-Hans.txt"
    output:
        DATA + "/counts/subtlex/zh.txt"
    shell:
        "xc simplify-chinese {input} {output}"

rule copy_europarl_pt:
    input:
        DATA + "/tokenized/opus/Europarl.pt-PT.txt"
    output:
        DATA + "/tokenized/opus/Europarl.pt.txt"
    shell:
        "cp {input} {output}"

# Handling similar data
# =====================

rule merge_news:
    input:
        lambda wildcards: multisource_counts_to_merge('news', wildcards.lang)
    output:
        DATA + "/counts/news/{lang}.txt"
    shell:
        "cat {input} | xc recount - {output} -l {wildcards.lang}"

rule merge_subtitles:
    input:
        lambda wildcards: multisource_counts_to_merge('subtitles', wildcards.lang)
    output:
        DATA + "/counts/subtitles/{lang}.txt"
    shell:
        "cat {input} | xc recount - {output} -l {wildcards.lang}"

rule merge_twitter:
    input:
        lambda wildcards: multisource_counts_to_merge('twitter', wildcards.lang)
    output:
        DATA + "/counts/twitter/{lang}.txt"
    shell:
        "cat {input} | xc recount - {output} -l {wildcards.lang}"

rule merge_web:
    input:
        lambda wildcards: multisource_counts_to_merge('web', wildcards.lang)
    output:
        DATA + "/counts/web/{lang}.txt"
    shell:
        "cat {input} | xc recount - {output} -l {wildcards.lang}"


# Assembling corpus text
# ======================

rule combine_reddit:
    input:
        expand(DATA + "/tokenized/reddit/{date}/{{lang}}.txt.gz",
               date=REDDIT_SHARDS)
    output:
        temp(DATA + "/tokenized/reddit/merged/{lang}.txt")
    priority:
        10
    run:
        if wildcards.lang == 'en':
            shell("zcat {input} | split -n r/1/50 > {output}")
        else:
            shell("zcat {input} > {output}")

rule shuffle_full_text:
    input:
        lambda wildcards: language_text_sources(wildcards.lang)
    output:
        DATA + "/shuffled/{lang}.txt"
    shell:
        "grep -h '.' {input} | scripts/imperfect-shuffle.sh {output} {wildcards.lang}"

rule fasttext_skipgrams:
    input:
        DATA + "/shuffled/{lang}.txt"
    output:
        DATA + "/skipgrams/{lang}.vec",
        DATA + "/skipgrams/{lang}.bin"
    run:
        if wildcards.lang == 'en':
            shell("fasttext skipgram -dim 300 -input {input} -output {DATA}/skipgrams/{wildcards.lang}")
        else:
           shell("fasttext skipgram -dim 200 -epoch 20 -input {input} -output {DATA}/skipgrams/{wildcards.lang}")


# Building wordfreq data files
# ============================

rule make_small_wordfreq_list:
    input:
        DATA + "/freqs/{lang}.txt"
    output:
        DATA + "/wordfreq/small_{lang}.msgpack.gz"
    shell:
        "xc export-to-wordfreq {input} - -c 600 | gzip -c > {output}"

rule make_large_wordfreq_list:
    input:
        DATA + "/freqs/{lang}.txt"
    output:
        DATA + "/wordfreq/large_{lang}.msgpack.gz"
    shell:
        "xc export-to-wordfreq {input} - -c 800 | gzip -c > {output}"

rule make_twitter_wordfreq_list:
    input:
        DATA + "/freqs/twitter/{lang}.txt"
    output:
        DATA + "/wordfreq/twitter_{lang}.msgpack.gz"
    shell:
        "xc export-to-wordfreq {input} - -c 600 | gzip -c > {output}"

rule make_jieba_list:
    input:
        DATA + "/freqs/{lang}.txt"
    output:
        DATA + "/wordfreq/jieba_{lang}.txt"
    shell:
        "xc export-to-jieba {input} {output} -c 600"


ruleorder:
    count_to_freqs > merge_freqs > merge_web > merge_reddit > \
    merge_subtlex_en > merge_opensubtitles_pt > merge_opensubtitles_zh > merge_globalvoices_zh > \
    merge_news > merge_subtitles > merge_twitter > \
    tokenize_twitter_v2_balkans > tokenize_twitter_v2 > \
    combine_reddit > copy_google_zh > copy_tatoeba_zh > copy_europarl_pt > \
    extract_google_1grams > count_tokens > recount_messy_tokens

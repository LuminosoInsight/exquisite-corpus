from wordfreq.tokens import tokenize
import fasttext
from ftfy import fix_text
from ftfy.fixes import unescape_html, fix_surrogates
import langcodes
import gzip
import sentencepiece
import msgpack

from .language_detection import detect_language, CLD2_LANGUAGES


def tokenize_file(
    infile, outfile, language, check_language=False, punctuation=False, ftfy=False
):
    """
    Take in a file of plain text, tokenize it as the given language, and write
    the result as lines of space-separated tokens.
    """
    for line in infile:
        if ftfy:
            # Run all ftfy fixes, but don't let it introduce line breaks
            line = fix_text(line.rstrip()).replace('\n', ' ')
        else:
            # Run only specific quick fixes from ftfy
            line = fix_surrogates(unescape_html(line.rstrip()))
        tokens = tokenize(
            line, language, include_punctuation=punctuation, external_wordlist=True
        )
        checked_lang = None
        if check_language:
            checked_lang, _confident = detect_language(line.rstrip())
        if (not check_language) or langcodes.tag_match_score(
            checked_lang, language
        ) >= 90:
            print(' '.join(tokens), file=outfile)


def tokenize_by_language(in_file, out_dir, zipped=False, languages=CLD2_LANGUAGES):
    """
    Take in language-tagged text, and use wordfreq to tokenize it.
    """
    if zipped:
        out_files = {
            language: gzip.open(
                '%s/%s.txt.gz' % (out_dir, language), 'wt', encoding='utf-8'
            )
            for language in languages
        }
    else:
        out_files = {
            language: open('%s/%s.txt' % (out_dir, language), 'w', encoding='utf-8')
            for language in languages
        }
    try:
        for line in in_file:
            lang, text = line.rstrip().split('\t', 1)
            if lang in languages:
                tokenized = tokenize(
                    text, lang, include_punctuation=True, external_wordlist=True
                )
                out_file = out_files[lang]
                print(' '.join(tokenized), file=out_file)
    finally:
        for out_file in out_files.values():
            out_file.close()


def tokenize_with_sentencepiece(in_file, out_file, sp_model_filename):
    """
    Take in monolingual plain text, and break it into SentencePiece tokens
    with the given model.
    """
    sp = sentencepiece.SentencePieceProcessor()
    sp.load(sp_model_filename)
    packer = msgpack.Packer()
    for line in in_file:
        ids = sp.encode_as_ids(line.rstrip())
        out_file.write(packer.pack(ids))


def map_to_fasttext_language(lang):
    """
    Map both 'zh-Hans' and 'zh-Hant' to 'zh' for fastText language identification.
    """
    mapping = {
        'zh-Hans': 'zh',
        'zh-Hant': 'zh'
    }
    return mapping.get(lang, lang)


def cleanup_parallel_file(
        infile, outfile, fasttext_model_file, lang1, lang2
):
    """
    Take in a tab-separated parallel text, run ftfy over each line, and skip the line if
    the text on either side contains different numbers of '♪' or if languages on either
    side are not identified with confidence.
    """
    # Load the FastText's language identification model
    fasttext_model = fasttext.load_model(fasttext_model_file)

    for line in infile:
        # Run all ftfy fixes
        line = fix_text(line)

        # '♪' mostly occurs only on the English side of the file. So, the X-to-English
        # translation model learns to translate 'something else' to this symbol. To
        # avoid that, skip any parallel line if text on either side contains different
        # numbers of '♪'.
        parallel_language_pair = line.split('\t')

        count1 = parallel_language_pair[0].count('♪')
        count2 = parallel_language_pair[1].count('♪')
        note_match = count1 == count2

        # There can be mixed or wrong language in source and/or target; including
        # untranslated source in the target. So, make sure that the sentences on both
        # sides consist of the right language.
        lang1_pred = fasttext_model.predict(
            parallel_language_pair[0].replace('\n', ' ').lower()
        )
        lang1_pred_code = lang1_pred[0][0][-2:]
        lang1_pred_prob = lang1_pred[1][0]

        lang2_pred = fasttext_model.predict(
            parallel_language_pair[1].replace('\n', ' ').lower()
        )
        lang2_pred_code = lang2_pred[0][0][-2:]
        lang2_pred_prob = lang2_pred[1][0]

        # Match with fastText language code
        lang1 = map_to_fasttext_language(lang1)
        lang2 = map_to_fasttext_language(lang2)

        # Threshold to say that the language has been identified with confidence
        lg_id_threshold = 0.70
        clean_lang1 = lang1_pred_code == lang1 and lang1_pred_prob >= lg_id_threshold
        clean_lang2 = lang2_pred_code == lang2 and lang2_pred_prob >= lg_id_threshold

        if note_match and clean_lang1 and clean_lang2:
            outfile.write(line)


def train_sentencepiece(in_file, model_prefix, lang):
    """
    Train SentencePiece unigram model. Input is raw corpus file, one sentence per line.
    Outputs are model and vocabulary files (<prefix>.model and <prefix>.vocab).
    Maximum size of sentences the trainer loads, by randomly sampling input sentences,
    is 1M. Vocabulary size is 32K and is a soft limit.
    It uses NFKC normalization with some additional normalization around spaces and
    Unicode case folding (mostly lower casing).
    """
    # 'character_coverage' is the amount of characters covered by the SentencePiece
    # model. Setting it to 1.0 will include all the characters in the training dataset.
    # As the dataset may contain many noisy/rare characters, we set it to 0.9994 for CJK
    # and 0.9999 for other languages with smaller character set.
    if lang in ['en_zh-Hans', 'en_zh-Hant', 'ja', 'ko']:
        lang_character_coverage = 0.9994
    else:
        lang_character_coverage = 0.9999

    parms = "--model_type=unigram " \
            "--input={file} " \
            "--model_prefix={prefix} " \
            "--input_format=text " \
            "--input_sentence_size=1000000 " \
            "--shuffle_input_sentence " \
            "--vocab_size=32000 " \
            "--hard_vocab_limit=false " \
            "--normalization_rule_name=nmt_nfkc_cf " \
            "--character_coverage={character_coverage}".format(
                file=in_file,
                prefix=model_prefix,
                character_coverage=lang_character_coverage
            )
    sentencepiece.SentencePieceTrainer.Train(parms)


def encode_with_sp_as_pieces(in_file, out_file, model_file):
    """
    Encode raw text into sentence pieces.
    """
    spp = sentencepiece.SentencePieceProcessor()
    spp.load(model_file)
    for line in in_file:
        pieces = spp.encode_as_pieces(line.rstrip())
        line_pieces = ' '.join(pieces) + '\n'
        out_file.write(line_pieces)


def decode_pieces_with_sp(in_file, out_file, model_file):
    """
    Decode sentence pieces into raw text.
    """
    spp = sentencepiece.SentencePieceProcessor()
    spp.load(model_file)
    for line in in_file:
        line_pieces = spp.decode_pieces(line.split()) + '\n'
        out_file.write(line_pieces)


def get_vocabulary_from_sp(out_file, model_file):
    """
    Get the vocabulary (one piece per line) to be used by the neural network.
    """
    spp = sentencepiece.SentencePieceProcessor()
    spp.load(model_file)
    # <unk>, <s>, </s> are defined by default and their ids are (0, 1, 2). Don't include
    # them in the vocabulary.
    for id in range(3, spp.get_piece_size()):
        pieces = spp.id_to_piece(id) + '\n'
        out_file.write(pieces)

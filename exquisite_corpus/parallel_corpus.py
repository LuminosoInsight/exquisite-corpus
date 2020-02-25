import sentencepiece
import fasttext
from ftfy import fix_text


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
    side are not identified with confidence (given text is long enough).
    """
    # Load the FastText's language identification model
    fasttext_model = fasttext.load_model(fasttext_model_file)

    for line in infile:
        # Run all ftfy fixes
        line = fix_text(line)

        # Replace any '\n' with space; else we will end up with one sided line in the
        # end
        line = line.replace('\n', ' ')

        # Make sure we have both sides
        parallel_language_pair = line.split('\t')
        if len(parallel_language_pair) != 2:
            continue

        # '♪' mostly occurs only on the English side of the file. So, the X-to-English
        # translation model learns to translate 'something else' to this symbol. To
        # avoid that, skip any parallel line if text on either side contains different
        # numbers of '♪'.
        lang1_sent = parallel_language_pair[0]
        lang2_sent = parallel_language_pair[1]

        count1 = lang1_sent.count('♪')
        count2 = lang2_sent.count('♪')
        note_match = count1 == count2

        # There can be mixed or wrong language in source and/or target; including
        # untranslated source in the target. So, make sure that the sentences on both
        # sides consist of the right language.
        clean_lang1 = True
        clean_lang2 = True

        # Minimum length to perform language identification
        min_length = 25

        # Threshold to say that the language has been identified with confidence
        id_threshold = 0.70

        len_lang1_sent = len(lang1_sent.encode('utf-8'))
        len_lang2_sent = len(lang2_sent.encode('utf-8'))
        if len_lang1_sent > min_length:
            lang1_pred = fasttext_model.predict(lang1_sent.replace('\n', ' ').lower())
            lang1_pred_code = lang1_pred[0][0][-2:]
            lang1_pred_prob = lang1_pred[1][0]

            lang1 = map_to_fasttext_language(lang1)
            clean_lang1 = lang1_pred_code == lang1 and lang1_pred_prob >= id_threshold

        if len_lang2_sent > min_length:
            lang2_pred = fasttext_model.predict(lang2_sent.replace('\n', ' ').lower())
            lang2_pred_code = lang2_pred[0][0][-2:]
            lang2_pred_prob = lang2_pred[1][0]

            lang2 = map_to_fasttext_language(lang2)
            clean_lang2 = lang2_pred_code == lang2 and lang2_pred_prob >= id_threshold

        # Require the source and target length ratio to not exceed 2.0. This also makes
        # sure that there are no empty source or target side so that fast_align would
        # not throw an error.
        ratio = 0.0
        if len_lang2_sent != 0:
            ratio = len_lang1_sent / len_lang2_sent
        balanced = 0.5 < ratio < 2.0

        # Input to fast_align must be tokenized and aligned into parallel sentences.
        # Each line is a source and target separated by a triple pipe symbol with
        # leading and trailing white space ( ||| ). To generate these, we paste two
        # files together and replace '\t' with this symbol. For this to work (see rule
        # join_training_data), we want to make sure that there are no additional '\t'
        # in the source or target side.
        no_tab = '\t' not in lang1_sent and '\t' not in lang2_sent

        if note_match and clean_lang1 and clean_lang2 and balanced and no_tab:
            outfile.write(line + '\n')


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
    if lang in ['zh-Hans', 'zh-Hant', 'ja', 'ko']:
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

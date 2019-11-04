import os
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

        # '♪' mostly occurs only on the English side of the file. So, the X-to-English
        # translation model learns to translate 'something else' to this symbol. To
        # avoid that, skip any parallel line if text on either side contains different
        # numbers of '♪'.
        parallel_language_pair = line.split('\t')
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

        if len(lang1_sent.encode('utf-8')) > min_length:
            lang1_pred = fasttext_model.predict(lang1_sent.replace('\n', ' ').lower())
            lang1_pred_code = lang1_pred[0][0][-2:]
            lang1_pred_prob = lang1_pred[1][0]

            lang1 = map_to_fasttext_language(lang1)
            clean_lang1 = lang1_pred_code == lang1 and lang1_pred_prob >= id_threshold

        if len(lang2_sent.encode('utf-8')) > min_length:
            lang2_pred = fasttext_model.predict(lang2_sent.replace('\n', ' ').lower())
            lang2_pred_code = lang2_pred[0][0][-2:]
            lang2_pred_prob = lang2_pred[1][0]

            lang2 = map_to_fasttext_language(lang2)
            clean_lang2 = lang2_pred_code == lang2 and lang2_pred_prob >= id_threshold

        if note_match and clean_lang1 and clean_lang2:
            outfile.write(line)


def sample_multilingual(in_files, out_file):
    """
    Take in tab-separated parallel text files and oversample the data from all language
    pairs to be of the same size as the largest language pair.
    """
    files = []
    line_count = []
    for file in in_files:
        # ar_en, cs_en, and de_en have English text on the right side of the
        # tab-separated parallel text file. The following step is needed to ensure
        # that English is on the left side of the multi-lingual dataset for all
        # language pairs.
        basename = os.path.basename(file)
        basename_root = os.path.splitext(basename)[0]
        first_lang = basename_root.split('_')[0]
        second_lang = basename_root.split('_')[1]

        if first_lang != 'en':
            tmp_dir = os.path.join('data', 'tmp')
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)

            new_file = os.path.join(tmp_dir, second_lang + '_' + first_lang + '.txt')
            lines = 0
            with open(new_file, 'w', encoding='utf-8') as file_new:
                with open(file, 'r', encoding='utf-8') as file_old:
                    for line in file_old:
                        lines += 1
                        sequences = line.replace('\n', '').split('\t')
                        file_new.write(sequences[1]+'\t'+sequences[0]+'\n')
            line_count.append(lines)
            files.append(new_file)
        else:
            line_count.append(len(open(file).readlines()))
            files.append(file)

    # Oversample the data from all language pairs to be of the same size as the largest
    # language pair. To ensure homogeneity, files are added in a continuous fashion (and
    # shuffled later).
    max_line_count = max(line_count)
    count = [0] * len(files)
    balanced = False
    while not balanced:
        for i in range(len(files)):
            with open(files[i], 'r', encoding='utf-8') as file:
                for line in file:
                    if count[i] == max_line_count:
                        break
                    out_file.write(line)
                    if line[-1] != '\n':
                        out_file.write('\n')
                    count[i] += 1
        balanced = all([True if c == max_line_count else False for c in count])


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

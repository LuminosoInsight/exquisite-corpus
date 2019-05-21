from wordfreq.tokens import tokenize
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


def tokenize_by_language(in_file, out_dir, zipped=False):
    """
    Take in language-tagged text, and use wordfreq to tokenize it.
    """
    if zipped:
        out_files = {
            language: gzip.open(
                '%s/%s.txt.gz' % (out_dir, language), 'wt', encoding='utf-8'
            )
            for language in CLD2_LANGUAGES
        }
    else:
        out_files = {
            language: open('%s/%s.txt' % (out_dir, language), 'w', encoding='utf-8')
            for language in CLD2_LANGUAGES
        }
    try:
        for line in in_file:
            lang, text = line.rstrip().split('\t', 1)
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


def train_sentencepiece(in_file, model_prefix):
    parms = "--input={} --model_prefix={} --vocab_size=8000 --hard_vocab_limit=false".format(in_file, model_prefix)
    sentencepiece.SentencePieceTrainer.Train(parms)


def encode_with_sp_as_pieces(in_file, out_file, model_file):
    spp = sentencepiece.SentencePieceProcessor()
    spp.load(model_file)
    for line in in_file:
        pieces = spp.encode_as_pieces(line.rstrip())
        line_pieces = ' '.join(pieces) + '\n'
        out_file.write(line_pieces)


def decode_pieces_with_sp(in_file, out_file, model_file):
    spp = sentencepiece.SentencePieceProcessor()
    spp.load(model_file)
    for line in in_file:
        line_pieces = spp.decode_pieces(line.split()) + '\n'
        out_file.write(line_pieces)


def get_vocabulary_from_sp(out_file, model_file):
    spp = sentencepiece.SentencePieceProcessor()
    spp.load(model_file)
    # <unk>, <s>, </s> are defined by default. Their ids are (0, 1, 2)
    for id in range(3, spp.get_piece_size()):
        pieces = spp.id_to_piece(id) + '\n'
        out_file.write(pieces)

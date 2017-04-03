import pathlib
import itertools
import struct
from ordered_set import OrderedSet


def make_uri(language, word):
    return '/c/{}/{}'.format(language, word)


def make_sparse_assoc(freq_path, parallel_text_path, output_path, languages, vocab_size=100000):
    print("Building vocab")
    vocab = OrderedSet()
    languages.sort()
    for language in languages:
        print('\t{}'.format(language))
        language_freq_path = freq_path / '{}.txt'.format(language)
        with language_freq_path.open(encoding='utf-8') as freq_file:
            for i, line in enumerate(freq_file):
                if i >= vocab_size:
                    break
                word, _rest = line.split('\t')
                uri = make_uri(language, word)
                vocab.add(uri)

    vocab_path = output_path / 'vocab.txt'
    with vocab_path.open('w', encoding='utf-8') as vocab_out:
        for uri in vocab:
            print(uri, file=vocab_out)

    coords_path = output_path / 'coords.dat'
    with (output_path / 'coords.dat').open('wb') as coords_out:
        for lang1, lang2 in itertools.combinations(languages, 2):
            print(lang1, lang2)
            parallel_path = parallel_text_path / '{}-{}.txt'.format(lang1, lang2)
            with parallel_path.open(encoding='utf-8') as parallel_file:
                for i, line in enumerate(parallel_file):
                    if i % 100000 == 0:
                        print('\t{}'.format(i))
                    text1, text2 = line.rstrip('\n').split('\t')
                    words1 = [make_uri(lang1, word) for word in text1]
                    words2 = [make_uri(lang2, word) for word in text1]
                    words = [uri for uri in (words1 + words2) if uri in vocab]
                    for word1 in words:
                        idx1 = vocab.index(word1)
                        for word2 in words:
                            idx2 = vocab.index(word2)
                            coord_bytes = struct.pack('<ii', idx1, idx2)
                            coords_out.write(coord_bytes)


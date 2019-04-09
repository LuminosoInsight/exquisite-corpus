from collections import defaultdict
from operator import itemgetter
from ftfy.fixes import uncurl_quotes
import math
import msgpack
import statistics


def merge_freqs(freq_dicts):
    """
    Merge multiple dictionaries of frequencies, representing each word with
    the 'figure skating average' of the word's frequency over all sources,
    meaning that we drop the highest and lowest values and average the rest.
    """
    vocab = set()
    for freq_dict in freq_dicts:
        vocab.update(freq_dict)

    merged = defaultdict(float)
    N = len(freq_dicts)
    if N < 3:
        raise ValueError(
            "Merging frequencies requires at least 3 frequency lists."
        )
    for term in vocab:
        freqs = []
        for freq_dict in freq_dicts:
            freq = freq_dict.get(term, 0.)
            freqs.append(freq)

        if freqs:
            freqs.sort()
            inliers = freqs[1:-1]
            mean = statistics.mean(inliers)
            if mean > 0.:
                merged[term] = mean

    total = sum(merged.values())

    # Normalize the merged values so that they add up to 0.99 (based on
    # a rough estimate that 1% of tokens will be out-of-vocabulary in a
    # wordlist of this size).
    for term in merged:
        merged[term] = merged[term] / total * 0.99
    return merged


def count_files_to_freqs(input_filenames, output_filename):
    """
    Take in multiple files of word counts by their filename, and produce a
    frequency list in the named output file. The counts should be in the format
    we produce that has a __total__ at the top. We merge them into a single
    frequency list using the 'figure skating average' defined above.
    """
    freq_dicts = []
    for input_filename in input_filenames:
        freq_dict = defaultdict(float)
        with open(input_filename, encoding='utf-8') as infile:
            total = None
            for line in infile:
                word, strcount = line.rstrip().split('\t', 1)
                # Correct for earlier steps that might not have handled curly
                # apostrophes consistently
                word = uncurl_quotes(word).strip("' ")
                if word:
                    count = int(strcount)
                    if word == '__total__':
                        total = count
                    else:
                        freq = count / total
                        if freq < 1e-9:
                            break
                        freq_dict[word] += freq
        freq_dicts.append(freq_dict)

    merged_dict = merge_freqs(freq_dicts)
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        _write_frequency_file(merged_dict, outfile)


def single_count_file_to_freqs(input_file, output_file):
    """
    Convert a single file of word counts (given as an open stream) to a
    file of frequencies.
    """
    total = None
    freq_dict = defaultdict(float)
    for line in input_file:
        word, strcount = line.rstrip().split('\t', 1)
        count = int(strcount)
        if word == '__total__':
            total = count
        else:
            freq = count / total
            if freq < 1e-9:
                break
            freq_dict[word] += freq

    _write_frequency_file(freq_dict, output_file)


def _write_frequency_file(freq_dict, outfile):
    freq_items = sorted(freq_dict.items(), key=itemgetter(1), reverse=True)
    for word, freq in freq_items:
        if freq < 1e-9:
            break
        print('{}\t{:.5g}'.format(word, freq), file=outfile)


def freqs_to_cBpack(input_file, output_file, cutoff=600):
    """
    Convert a frequency list into the idiosyncratic 'cBpack' format that
    will be loaded by wordfreq: a list in msgpack format of frequency
    tiers, each tier being one centibel (a factor of 10^(1/100))
    less frequent than the previous tier.
    """
    cBpack = []
    for line in input_file:
        word, strfreq = line.rstrip().split('\t', 1)
        if word == '__total__':
            raise ValueError(
                "This is a count file, not a frequency file"
            )
        freq = float(strfreq)
        neg_cB = -(round(math.log10(freq) * 100))
        if neg_cB >= cutoff:
            break
        while neg_cB >= len(cBpack):
            cBpack.append([])
        cBpack[neg_cB].append(word)

    for sublist in cBpack:
        sublist.sort()

    cBpack_data = [{'format': 'cB', 'version': 1}] + cBpack

    msgpack.dump(cBpack_data, output_file)


def freqs_to_jieba(input_file, output_file, cutoff=600):
    """
    Convert a frequency list into the format expected by Jieba, a Chinese
    word segmenter for Python.
    """
    for line in input_file:
        word, strfreq = line.rstrip().split('\t', 1)
        if word == '__total__':
            raise ValueError(
                "This is a count file, not a frequency file"
            )
        if not word.strip():
            continue
        freq = float(strfreq)
        neg_cB = -(math.log10(freq) * 100)
        if neg_cB >= cutoff:
            break
        int_freq = round(freq * 1e9)
        print("%s %d" % (word, int_freq), file=output_file)


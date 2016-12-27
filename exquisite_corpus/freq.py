from collections import defaultdict
from operator import itemgetter
from ftfy.fixes import uncurl_quotes
import statistics


def merge_freqs(freq_dicts):
    """
    Merge multiple dictionaries of frequencies, representing each word with
    the median of the word's frequency over all sources.
    """
    vocab = set()
    for freq_dict in freq_dicts:
        vocab.update(freq_dict)

    merged = defaultdict(float)
    N = len(freq_dicts)
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


def merge_count_files_to_freqs(input_filenames, output_filename):
    """
    Take in multiple files of word counts, in the format we produce that has a
    __total__ at the top, and merge them into a single frequency list using
    the sorta-median approach.
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
                        if word in freq_dict:
                            freq_dict[word] += freq
                        else:
                            freq_dict[word] = freq
        freq_dicts.append(freq_dict)

    merged_dict = merge_freqs(freq_dicts)
    freq_items = sorted(merged_dict.items(), key=itemgetter(1), reverse=True)
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for word, freq in freq_items:
            if freq < 1e-9:
                break
            print('{}\t{:.5g}'.format(word, freq), file=outfile)


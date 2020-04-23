from functools import partial
from modAL.models import ActiveLearner
from modAL.uncertainty import uncertainty_sampling
from modAL.batch import uncertainty_batch_sampling
from math import log2
from sklearn.svm import NuSVC
from sklearn.neural_network import MLPClassifier
from imblearn.under_sampling import RandomUnderSampler
import numpy as np
import json
import pickle

# input features: the -log2 of FTLID's believed probability that it was is wrong, the number of characters,
# and the number of spaces

def log_info(probability):
    if probability >= 1.:
        return 20.
    else:
        return min(20., -log2(1. - probability))


def load_unlabeled(filename):
    inputs = []
    texts = []
    text_set = set()
    for line in open(filename, encoding='utf-8'):
        line = line.strip()
        if line:
            obj = json.loads(line)
            text = obj['text']
            if text not in text_set:
                text_length = len(text)
                info = log_info(obj['language_confidence'])
                spaces = text.count(' ')
                inputs.append((text_length, info, spaces))
                texts.append(text)
                text_set.add(text)

    return np.array(inputs), texts


def load_labeled_dataframes(filenames):
    X_labeled = []
    y_labeled = []
    for filename in filenames:
        df = pickle.load(open(filename, 'rb'))
        for row_label in df.index:
            row = df.loc[row_label]
            info = log_info(row['pred_confidence_raw'])
            X_labeled.append([row['length'], info, row['white_spaces']])
            label = row['pred_lang_raw'] == row['true_lang']
            y_labeled.append(label)
    return np.array(X_labeled), np.array(y_labeled)


def load_annotated(filename):
    X_labeled = []
    y_labeled = []
    for line in open(filename):
        length_str, info_str, spaces_str, label_str = line.strip().split('\t')
        length = int(float(length_str))
        info = float(info_str)
        spaces = int(float(spaces_str))
        label = (label_str == 'True')
        X_labeled.append([length, info, spaces])
        y_labeled.append(label)
    return np.array(X_labeled), np.array(y_labeled)


def learning_loop(labeled_filenames, data_filename, output_filename):
    input_train1, output_train1 = load_labeled_dataframes(labeled_filenames)
    try:
        input_train2, output_train2 = load_annotated(output_filename)
        input_train = np.concatenate([input_train1, input_train2])
        output_train = np.concatenate([output_train1, output_train2], axis=0)
    except FileNotFoundError:
        input_train = input_train1
        output_train = output_train1
    print(np.sum(output_train) / len(output_train))
    preset_batch = partial(uncertainty_sampling, n_instances=20)
    learner = ActiveLearner(
        estimator=MLPClassifier(hidden_layer_sizes=(5,), alpha=0.01, max_iter=1000),
        query_strategy=preset_batch,
        X_training=input_train,
        y_training=output_train,
    )
    model_accuracy = learner.score(input_train, output_train)
    print(learner.estimator.classes_)
    print(f'Accuracy so far: {model_accuracy:3.3f}')
    data_pool, data_texts = load_unlabeled(data_filename)
    print('starting sampling')
    with open(output_filename, 'a') as out:
        while True:
            query_idxs, query_insts = learner.query(data_pool)
            responses = []
            for i in range(len(query_idxs)):
                query_idx = query_idxs[i]
                print(repr(data_texts[query_idx]))
                text_length, info, spaces = query_insts[i]
                print(f'Length: {text_length}\tSpaces: {spaces}\tConfidence: {info:3.3f}')
                human_input = input("Is the label correct? ")
                gold_label = human_input in ('y', 'Y', '1', 't', 'T') or human_input.startswith('y')
                responses.append(gold_label)
                print(f'{text_length}\t{info}\t{spaces}\t{gold_label}', file=out)
                print()
            
            learner.teach(query_insts, np.array(responses))
            out.flush()

            data_pool = np.delete(data_pool, query_idxs, axis=0)
            query_idxs = list(query_idxs)
            query_idxs.sort(reverse=True)
            for idx in query_idxs:
                data_texts.pop(idx)


if __name__ == '__main__':
    import sys
    lang = sys.argv[1]
    learning_loop(
        [f'analysis-output-{source}.pkl' for source in ['tatoeba', 'twitter', 'wikipedia']],
        f'/home/rspeer/code/twitter_stream_collector/twitterlogs/tweets.{lang}.jsonl',
        f'annotated-{lang}.tsv'
    )

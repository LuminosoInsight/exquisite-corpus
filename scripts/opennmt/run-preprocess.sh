script_path=$(dirname "$0")
$script_path/preprocess.py -train_src parallel-en-$1/train.$1 -train_tgt parallel-en-$1/train.en -valid_src parallel-en-$1/valid.$1 -valid_tgt parallel-en-$1/valid.en -save_data parallel-en-$1/save -max_shard_size 5000000

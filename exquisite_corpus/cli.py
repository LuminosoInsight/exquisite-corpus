import click
from .tokens import tokenize_file, tokenize_by_language
from .sparse_assoc import make_sparse_assoc, intersperse_parallel_text
from .count import count_tokenized, recount_messy
from .freq import (
    count_files_to_freqs, single_count_file_to_freqs, freqs_to_cBpack,
    freqs_to_jieba
)
from wordfreq.chinese import simplify_chinese
import os
import pathlib


@click.group()
def cli():
    pass


@cli.command(name='tokenize')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
@click.option('--language', '-l')
@click.option('--check-language', '-c', is_flag=True, default=False)
@click.option('--punctuation/--no-punctuation', '-p', is_flag=True, default=False)
@click.option('--ftfy', '-f', is_flag=True, default=False)
def run_tokenize(input_file, output_file, language, check_language, punctuation, ftfy):
    tokenize_file(input_file, output_file, language, check_language, punctuation, ftfy=ftfy)


@cli.command(name='tokenize-by-language')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_dir', type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True))
@click.option('--mode', '-m', type=click.Choice(['twitter', 'reddit', 'amazon']), default='twitter')
def run_tokenize_by_language(input_file, output_dir, mode):
    os.makedirs(output_dir, exist_ok=True)
    tokenize_by_language(input_file, output_dir, mode)


@cli.command(name='count')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
def run_count(input_file, output_file):
    count_tokenized(input_file, output_file)


@cli.command(name='recount')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
@click.option('--language', '-l', default='en')
def run_recount(input_file, output_file, language):
    recount_messy(input_file, output_file, language)


@cli.command(name='count-to-freqs')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
def run_count_to_freqs(input_file, output_file):
    single_count_file_to_freqs(input_file, output_file)


@cli.command(name='merge-freqs')
@click.argument('input_filenames', type=click.Path(readable=True, dir_okay=False), nargs=-1)
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
def run_merge_freqs(input_filenames, output_filename):
    count_files_to_freqs(input_filenames, output_filename)


@cli.command(name='export-to-wordfreq')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('wb'), default='-')
@click.option('--cutoff', '-c', type=int, default=600)
def run_export_to_wordfreq(input_file, output_file, cutoff):
    freqs_to_cBpack(input_file, output_file, cutoff)


@cli.command(name='export-to-jieba')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
@click.option('--cutoff', '-c', type=int, default=600)
def run_export_to_jieba(input_file, output_file, cutoff):
    freqs_to_jieba(input_file, output_file, cutoff)


@cli.command(name='simplify-chinese')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
def run_simplify_chinese(input_file, output_file):
    for line in input_file:
        line = line.rstrip()
        print(simplify_chinese(line), file=output_file)


@cli.command(name='sparse-assoc')
@click.argument('parallel_text_dir', type=click.Path(readable=True, dir_okay=True, file_okay=False))
@click.argument('vocab_dir', type=click.Path(readable=True, dir_okay=True, file_okay=False))
@click.argument('output_dir', type=click.Path(writable=True, dir_okay=True, file_okay=False))
@click.option('--languages', '-l', default='de,en,es,it,fa')
@click.option('--vocab_size', '-s', type=int, default=100000)
def run_sparse_assoc(parallel_text_dir, vocab_dir, output_dir, languages, vocab_size):
    language_list = languages.split(',')
    make_sparse_assoc(
        pathlib.Path(vocab_dir),
        pathlib.Path(parallel_text_dir),
        pathlib.Path(output_dir),
        language_list,
        vocab_size
    )


@cli.command(name='intersperse')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
@click.argument('lang1')
@click.argument('lang2')
def run_intersperse(input_file, output_file, lang1, lang2):
    intersperse_parallel_text(input_file, output_file, lang1, lang2)



import click
from .tokens import tokenize_file, tokenize_by_language
from .count import count_tokenized, recount_messy
from wordfreq.chinese import simplify_chinese
import os


@click.group()
def cli():
    pass


@cli.command(name='tokenize')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
@click.option('--language', '-l')
def run_tokenize(input_file, output_file, language):
    tokenize_file(input_file, output_file, language)


@cli.command(name='tokenize-by-language')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_dir', type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True))
@click.option('--mode', '-m', type=click.Choice(['twitter', 'reddit']), default='twitter')
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


@cli.command(name='simplify-chinese')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
def run_simplify_chinese(input_file, output_file):
    for line in input_file:
        line = line.rstrip()
        print(simplify_chinese(line), file=output_file)


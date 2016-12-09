import click
from .filters import tokenize_file, scan_xml2
from .count import count_tokenized, recount_messy


@click.group()
def cli():
    pass


@cli.command(name='tokenize')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
@click.option('--language', '-l')
def run_tokenize(input_file, output_file, language):
    tokenize_file(input_file, output_file, language)


@cli.command(name='count')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
def run_count(input_file, output_file):
    count_tokenized(input_file, output_file)


@cli.command(name='recount')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
def run_recount(input_file, output_file):
    recount_messy(input_file, output_file)

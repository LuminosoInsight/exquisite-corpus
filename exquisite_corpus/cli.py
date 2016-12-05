import click
from .filters import tokenize_file, scan_xml2

@click.group()
def cli():
    pass


@cli.command(name='tokenize')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
@click.option('--language', '-l')
def run_tokenize(input_file, output_file, language):
    tokenize_file(input_file, output_file, language)


@cli.command(name='scan_xml2')
@click.argument('input_file', type=click.File('r', encoding='utf-8'), default='-')
@click.argument('output_file', type=click.File('w', encoding='utf-8'), default='-')
def run_scan_xml2(input_file, output_file):
    scan_xml2(input_file, output_file)


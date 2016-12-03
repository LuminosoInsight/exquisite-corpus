import click
from .filters import tokenize_file

@click.group()
def cli():
    pass


@cli.command(name='tokenize')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
def run_tokenize(input_filename, output_filename):
    tokenize_file(input_filename, output_filename)

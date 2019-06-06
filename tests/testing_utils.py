import glob

import subprocess


def run_snakemake(env_variables, options=['-j', '4'], target=''):
    cmd_args = ["snakemake"] + options
    if target:
        cmd_args.append(target)
    subprocess.call(cmd_args, env=env_variables)


def gzipped_result_dir_same_as_reference(result, reference):
    """
    Return True if all gzipped files in result directory matched the gzipped files in
    the reference directory and False otherwise.
    """
    result_files = sorted(glob.glob(result + '/**/*.gz', recursive=True))
    reference_files = sorted(glob.glob(reference + '/**/*.gz', recursive=True))
    return all(
        gzipped_result_file_same_as_reference(res, ref)
        for res, ref in zip(result_files, reference_files)
    )


def gzipped_result_file_same_as_reference(result, reference):
    """
    Return True if a gzipped file result matches the gzipped reference file and False
    otherwise. Do not compare a header of a gzipped file, which contains information
    on when the file was compressed.
    """
    cmd_args = ['cmp', '-i', '8']  # skip a header
    code = subprocess.call(cmd_args + [result, reference])
    return not bool(code)


def result_dir_same_as_reference(result, reference):
    """
    Return True if all text files in result directory matched the text files in the
    reference directory and False otherwise. Skip the gzipped files.
    """
    cmd_args = ['diff', '-r', '-x', '*.gz', '-q', '-N']
    code = subprocess.call(cmd_args + [result, reference])
    return not bool(code)

import subprocess
import os
import glob

def run_snakemake(snakefile='../Snakefile', target="all", **kwargs):
    """

    """
    options = kwargs.pop("options", [])
    cmd_args = ["snakemake", "-s", str(snakefile), target] + options
    return subprocess.call(cmd_args)


# def binary_files_the_same(result, reference):
#     """"
#     :param result:
#     :param reference:
#     :return:
#     """
#     res_file = open(result, 'r')
#     ref_file = open(reference, 'r')
#
#     compare the length of both files
    # len_res = os.stat(res_file.fileno()).st_size
    # len_ref = os.stat(ref_file.fileno()).st_size
    #
    # if len_res != len_ref:
    #     res_file.close()
    #     ref_file.close()
    #     return False
    #
    # read the contents of the files
    # content_res = res_file.read()
    # content_ref = ref_file.read()
    #
    # if content_res == content_ref:
    #     return True
    # else:
    #     return False

def directories_with_gzipped_files_the_same(result, reference):
    result_gzipped_files = sorted(glob.glob(result + '/**/*.gz',
                                            recursive=True))
    reference_gzipped_files = sorted(glob.glob(reference + '/**/*.gz',
                                               recursive=True))
    if not result_gzipped_files and not reference_gzipped_files:
        return False
    return all(gzipped_files_the_same(res, ref) for res, ref in zip(result_gzipped_files, reference_gzipped_files))


def gzipped_files_the_same(result, reference):
    """
    :param result:
    :param reference:
    :return:
    """
    # skip a header of a gzipped file which contains information on when the
    # file was compressed
    cmd_args = ['cmp', '-i', '8']
    code = subprocess.call(cmd_args + [result, reference])
    return not(bool(code))

def text_files_the_same(result, reference):
    """

    :param result:
    :param reference:
    :return:
    """
    cmd_args = ['diff', result, reference]
    code = subprocess.call(cmd_args)
    return not(bool(code))


def directories_the_same(result, reference):
    """

    :param result:
    :param reference:
    :return:
    """
    cmd_args = ['diff', '-r', '-x', '*.gz', '-q']
    code = subprocess.call(cmd_args + [result, reference])
    return not(bool(code))

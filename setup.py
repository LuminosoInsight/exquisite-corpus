from setuptools import setup

setup(
    name="exquisite_corpus",
    version='0.1',
    maintainer='Luminoso Technologies, Inc.',
    maintainer_email='rspeer@luminoso.com',
    platforms=["any"],
    description="Download and process many gigabytes of natural language data, assembled from various corpora.",
    packages=['exquisite_corpus'],
    include_package_data=True,
    install_requires=[
        'snakemake < 5.6', 'wordfreq[jieba,mecab] >= 2.3.2', 'click',
        'regex >= 2018.01.08', 'pycld2', 'msgpack-python', 'ordered-set',
        'ftfy', 'subword-nmt', 'sentencepiece', 'mmh3', 'pytest', 'tqdm', 'fasttext'
    ],
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'console_scripts': ['xc = exquisite_corpus.cli:cli'],
    },
)

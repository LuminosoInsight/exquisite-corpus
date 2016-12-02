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
    install_requires=['snakemake', 'wordfreq', 'click'],
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        'excorpus': ['excorpus = exquisite_corpus.cli:cli'],
    },
)

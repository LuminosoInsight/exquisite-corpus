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
    install_requires=['snakemake', 'wordfreq', 'click', 'regex >= 2016', 'pycld2'],
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        'console_scripts': ['xc = exquisite_corpus.cli:cli'],
    },
)

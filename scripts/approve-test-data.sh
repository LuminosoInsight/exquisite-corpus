#!/bin/bash

echo "Copying input files from tests/input_data"
rm -r tests/data/raw
rm -r tests/data/downloaded
rm -r tests/data/source-lists
cp -r tests/input_data/raw tests/data
cp -r tests/input_data/downloaded tests/data
cp -r tests/input_data/source-lists tests/data

echo "Running the build"
XC_BUILD_TEST="1" snakemake -j 4

echo "Copying the output files to tests/reference"
rm -r tests/reference/*
cp -r tests/data/extracted tests/reference
cp -r tests/data/tokenized tests/reference
cp -r tests/data/messy-counts tests/reference
cp -r tests/data/counts tests/reference
cp -r tests/data/freqs tests/reference
cp -r tests/data/wordfreq tests/reference

echo "Removing the output files from tests/data"
rm -r tests/data/extracted
rm -r tests/data/tokenized
rm -r tests/data/messy-counts
rm -r tests/data/counts
rm -r tests/data/freqs
rm -r tests/data/wordfreq
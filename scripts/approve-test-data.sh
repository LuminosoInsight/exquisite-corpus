#!/bin/bash

output_directories="extracted tokenized messy-counts counts freqs wordfreq"

echo "Copying the output directories to tests/reference"
rm -r tests/reference/*

for directory in $output_directories; do
    cp -r tests/data/$directory tests/reference
done

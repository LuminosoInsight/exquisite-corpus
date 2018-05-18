#!/bin/sh
snakemake $@ -j 4 --resources download=4 --resources opusdownload=1

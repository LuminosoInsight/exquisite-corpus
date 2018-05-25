#!/bin/sh
snakemake $@ -j 8 --resources download=4 --resources opusdownload=1

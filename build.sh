#!/bin/sh
snakemake $@ -j 8 --resources download=4 --resources opusdownload=1 --resources sp_trainer=1 --resources alignment=1

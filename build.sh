#!/bin/sh
snakemake $@ -j 8 --resources sp_trainer=1 --resources alignment=1 --resources download=1

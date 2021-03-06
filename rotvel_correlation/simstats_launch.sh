#!/usr/bin/env bash

echo -e "\e[91mRemoving outdated SLURM output records...\e[0m"
rm standard_*

echo -e "\e[1m\e[91mSubmitting script to SLURM...\e[0m"
sbatch ./simstats_schedule.sh

echo -e "\e[5m\e[1m\e[91mJob submitted.\e[0m"
squeue -u dc-alta2
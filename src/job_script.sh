#!/bin/sh
#$ -cwd
#$ -l cpu_40=1
#$ -l h_rt=24:00:00
#$ -N vina_run

. /etc/profile.d/modules.sh
source $HOME/.bashrc
conda activate vina

python src/queue_system.py --csv_file test/parameters.csv

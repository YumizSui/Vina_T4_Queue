# AutoDock Vina on TSUBAME 4.0

This repository provides scripts for managing and executing multiple molecular docking simulations in parallel using a job queuing system with AutoDock Vina on [TSUBAME 4.0](https://www.t4.gsic.titech.ac.jp).

## Environment Setup

1. **Create a Conda Environment**

Based on the [AutoDock Vina tutorial](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html), create a new Conda environment and install the necessary packages:

```bash
conda create -n vina python=3.9
conda activate vina
conda install -c conda-forge vina meeko
# Install portalocker for file locking
pip install portalocker
```

2. **Install ADFR**

Download and install [ADFR](https://ccsb.scripps.edu/adfr/downloads/). Ensure the `ADFRsuite` binaries are in your `PATH` or note their location.

## Preparation

The `test` directory contains examples of virtual screening targeting [CDK2](https://dude.docking.org/targets/cdk2) in the [DUD-E dataset](https://dude.docking.org/).

### Prepare Receptor

Convert the receptor PDB file to PDBQT format:

```bash
ADFR_DIR=/path/to/ADFRsuite/bin
$ADFR_DIR/prepare_receptor -r ./test/receptor.pdb -o ./test/receptor.pdbqt
```

### Prepare Ligands

Split multi-molecule mol2 files into individual mol2 files:

```bash
gzip -d ./test/actives_final.mol2.gz
gzip -d ./test/decoys_final.mol2.gz
python ./src/split_mol2.py --input_file ./test/actives_final.mol2 --output_dir ./test/mol2 --prefix actives_final_
python ./src/split_mol2.py --input_file ./test/decoys_final.mol2 --output_dir ./test/mol2 --prefix decoys_final_
```

This creates individual mol2 files for each molecule in the specified output directory (`./test/mol2`).

Convert mol2 files to PDBQT format:

```bash
python ./src/prepare_ligands.py --input_dir ./test/mol2 --output_dir ./test/pdbqt
```

The script processes all mol2 files in `./test/mol2` and outputs PDBQT files in `./test/pdbqt`.

## Job Execution

### Parameters CSV

Specify docking jobs in `test/parameters.csv`:

```csv
REC_FILE,CONFIG_FILE,INPUT_DIR,OUTPUT_DIR,status
test/receptor.pdbqt,test/input.txt,test/pdbqt,test/docked,pending
```

- **REC_FILE**: Path to the receptor PDBQT file.
- **CONFIG_FILE**: Path to the Vina configuration file.
- **INPUT_DIR**: Directory containing ligand PDBQT files.
- **OUTPUT_DIR**: Directory where docking results will be saved.
- **status**: Job status (`pending`, `in_progress`, `done`, or `failed`). Initial status should be `pending`.


### Command Template

The CSV parameters correspond to the command template in `src/queue_system.py`:

```python
command_template = "python src/vina_docking_parallel.py --receptor_file {REC_FILE} --config {CONFIG_FILE} --input_dir {INPUT_DIR} --output_dir {OUTPUT_DIR}"
```

- The script reads the CSV file and replaces the placeholders with the actual values.
- The initial `status` is `pending`. It changes to `in_progress` during execution and to `done` or `failed` upon completion.

**Note**: This system is designed for executing multiple docking configurations in parallel but is not intended for running large-scale screenings in parallel.

## Running Jobs on TSUBAME 4.0

Create a job script `job_script.sh`:

```bash
#!/bin/sh
#$ -cwd
#$ -l cpu_40=1
#$ -l h_rt=24:00:00
#$ -N vina_run

. /etc/profile.d/modules.sh
source $HOME/.bashrc
conda activate vina

python ./src/queue_system.py --csv_file ./test/parameters.csv --time_limit 86000
```

For more information on job submission, refer to the [TSUBAME4.0's User Guide](https://www.t4.gsic.titech.ac.jp/docs/handbook.ja/).

Submit jobs using:

`qsub -g [TSUBAME group] -t 1-10 ./src/job_script.sh`

- Replace `[TSUBAME group]` with your group name.
- The `-t 1-10` option runs 10 tasks in parallel.

import os
import sys
import subprocess
from tqdm import tqdm
import argparse
from multiprocessing import Pool

def process_file(task_details):
    """Process a single file using the specified command.

    Args:
        task_details (tuple): Contains the input file path, output file path, and command to run.

    Returns:
        int: The return code from the subprocess execution.
    """
    input_path, output_path, mkprep = task_details
    command = [mkprep, "-i", input_path, "-o", output_path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print(f"Error processing {input_path}: {result.returncode}\n{result.stderr.decode()}")

    return result.returncode

def main():
    """Main function to parse arguments and process files."""
    parser = argparse.ArgumentParser(description="Prepare ligands for docking using Vina.")
    parser.add_argument("--input_dir", default="../targets", help="Directory containing input files.")
    parser.add_argument("--output_dir", default="../targets", help="Directory where output files will be saved.")
    parser.add_argument("--input_suffix", default=".mol2", help="Suffix of input files.")
    parser.add_argument("--output_suffix", default=".pdbqt", help="Suffix for processed output files.")
    parser.add_argument("--mk_prepare_ligand", default="mk_prepare_ligand.py", help="Script to prepare ligands.")
    args = parser.parse_args()

    # Ensure the output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Prepare a list of tasks
    tasks = []
    for input_file in os.listdir(args.input_dir):
        if input_file.endswith(args.input_suffix):
            input_path = os.path.join(args.input_dir, input_file)
            output_file = input_file.replace(args.input_suffix, args.output_suffix)
            output_path = os.path.join(args.output_dir, output_file)
            if not os.path.exists(output_path):  # Skip if the output already exists
                tasks.append((input_path, output_path, args.mk_prepare_ligand))

    # Process the files with multiprocessing
    with Pool() as pool:
        list(tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="Processing files"))

if __name__ == "__main__":
    main()

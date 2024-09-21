import os
import sys
from tqdm import tqdm
from glob import glob
import argparse

def main():
    parser = argparse.ArgumentParser(description="Split a MOL2 file containing multiple ligands into separate files.")
    parser.add_argument("--input_file", type=str, required=True, help="Path to the input MOL2 file.")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to store the output MOL2 files.")
    parser.add_argument("--prefix", type=str, required=True, help="Prefix for the output files.")
    parser.add_argument("--suffix", type=str, default=".mol2", help="Suffix for the output files (default: .mol2).")
    args = parser.parse_args()

    # Verify input file exists
    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f"{args.input_file} not found")

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Read input file
    with open(args.input_file) as file:
        lines = file.read().splitlines()

    # Count the number of ligands in the input file
    total_ligands = lines.count('@<TRIPOS>MOLECULE')

    # Count already processed files
    existing_files_count = len(glob(os.path.join(args.output_dir, f"{args.prefix}*{args.suffix}")))
    if existing_files_count == total_ligands:
        print(f"Already split {existing_files_count} ligands.")
        sys.exit(0)

    # Start splitting
    print(f"Splitting {total_ligands} ligands")
    start_index = 0
    ligand_number = 0

    for idx, line in tqdm(enumerate(lines), total=len(lines)):
        if line == '@<TRIPOS>MOLECULE' and idx > 0:
            ligand_block = lines[start_index:idx]
            mol2_file_path = os.path.join(args.output_dir, f"{args.prefix}{ligand_number}{args.suffix}")
            with open(mol2_file_path, 'w') as mol_file:
                mol_file.write('\n'.join(ligand_block))
                mol_file.write("\n")
            ligand_number += 1
            start_index = idx

    # Handle the last ligand block
    ligand_block = lines[start_index:]
    mol2_file_path = os.path.join(args.output_dir, f"{args.prefix}{ligand_number}{args.suffix}")
    with open(mol2_file_path, 'w') as mol_file:
        mol_file.write('\n'.join(ligand_block))
        mol_file.write("\n")

if __name__ == "__main__":
    main()

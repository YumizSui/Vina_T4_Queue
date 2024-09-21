from tqdm import tqdm
import os
from vina import Vina
import argparse
import multiprocessing
from functools import partial

def parse_input(input_string):
    lines = input_string.strip().split('\n')
    parsed_data = {}

    for line in lines:
        key, value = line.split('=')
        key = key.strip()
        value = float(value.strip())
        parsed_data[key] = value

    return parsed_data

def process_ligand(ligand, receptor_file, center, box_size, input_dir, output_dir):
    ligand_file = f"{input_dir}/{ligand}"
    output_file = f"{output_dir}/{ligand}"
    if os.path.exists(output_file):
        return
    v = Vina(sf_name='vina', cpu=1, verbosity=0)
    v.set_receptor(receptor_file)
    v.set_ligand_from_file(ligand_file)
    v.compute_vina_maps(center=center, box_size=box_size)
    v.dock(exhaustiveness=8, n_poses=1)
    v.write_poses(output_file, overwrite=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--receptor_file", required=True)
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--threads", type=int, default=None)
    args = parser.parse_args()

    receptor_file = args.receptor_file
    input_dir = args.input_dir
    output_dir = args.output_dir

    with open(args.config) as f:
        inputdict = parse_input(f.read())

    print(f"Processing {args.input_dir} to {args.output_dir}, using {args.receptor_file}")
    center = [inputdict["center_x"], inputdict["center_y"], inputdict["center_z"]]
    box_size = [inputdict["size_x"], inputdict["size_y"], inputdict["size_z"]]

    os.makedirs(output_dir, exist_ok=True)

    ligands = sorted(os.listdir(input_dir))
    ligands = [ligand for ligand in ligands if not os.path.exists(f"{output_dir}/{ligand}")]

    # Prepare the partial function with fixed arguments
    func = partial(process_ligand, receptor_file=receptor_file, center=center,
                   box_size=box_size, input_dir=input_dir, output_dir=output_dir)

    # Use multiprocessing Pool to parallelize ligand processing
    with multiprocessing.Pool(args.threads) as pool:
        list(tqdm(pool.imap_unordered(func, ligands), total=len(ligands)))

if __name__ == "__main__":
    main()

import csv
import subprocess
import threading
import time
import portalocker
import os
import argparse

def acquire_parameter(csv_file):
    """
    Retrieve an unprocessed parameter from the CSV file and update its status to 'in_progress'.
    """
    with open(csv_file, 'r+', newline='') as csvfile:
        portalocker.lock(csvfile, portalocker.LOCK_EX)
        reader = list(csv.DictReader(csvfile))
        for row in reader:
            if row.get('status', 'pending') == 'pending':
                row['status'] = 'in_progress'
                fieldnames = reader[0].keys()
                csvfile.seek(0)
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(reader)
                csvfile.truncate()
                portalocker.unlock(csvfile)
                return row
        portalocker.unlock(csvfile)
    return None

def update_parameter_status(csv_file, param_row, status):
    """
    Update the status of a parameter.
    """
    with open(csv_file, 'r+', newline='') as csvfile:
        portalocker.lock(csvfile, portalocker.LOCK_EX)
        reader = list(csv.DictReader(csvfile))
        for row in reader:
            if all(row[key] == param_row[key] for key in param_row if key != 'status'):
                row['status'] = status
                break
        fieldnames = reader[0].keys()
        csvfile.seek(0)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)
        csvfile.truncate()
        portalocker.unlock(csvfile)

def run_job(param_row, command_template, time_limit, csv_file):
    """
    Execute a job and monitor the time limit.
    """
    command = command_template.format(**param_row).split()
    print("Running command: ", " ".join(command))
    try:
        subprocess.run(command, timeout=time_limit, check=True)
        update_parameter_status(csv_file, param_row, 'done')
    except subprocess.TimeoutExpired:
        print(f"Job exceeded the time limit. Re-adding the parameter to the queue: {param_row}")
        update_parameter_status(csv_file, param_row, 'pending')
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during job execution: {e}")
        update_parameter_status(csv_file, param_row, 'failed')

def main():
    parser = argparse.ArgumentParser(description='Job script for the queuing system')
    parser.add_argument('--csv_file', type=str, required=True, help='CSV file containing the parameter list')
    parser.add_argument('--time_limit', type=int, default=86000, help='Time limit for the job (seconds)')
    args = parser.parse_args()

    csv_file = args.csv_file
    time_limit = args.time_limit
    command_template = "python src/vina_docking_parallel.py --receptor_file {REC_FILE} --config {CONFIG_FILE} --input_dir {INPUT_DIR} --output_dir {OUTPUT_DIR}"

    while True:
        param_row = acquire_parameter(csv_file)
        if param_row is None:
            print("No unprocessed parameters available.")
            break
        print(f"Starting job: {param_row}")
        run_job(param_row, command_template, time_limit, csv_file)

if __name__ == '__main__':
    main()

""" Queue manager script

This script checks whether there are any molecular dynamics transformations to be sent in the queue. If there are, it
will send them in the queue to wait for being called by slurm manager. The transformations can be sent to either GPU
or CPU units, depending on the simulation and specified maximum limits.

The script is designed to manage the processing of transformations in a molecular dynamics simulation pipeline. It
connects to a database, identifies available transformations, and schedules them for processing on the available
computational units. It keeps track of the job status and updates it accordingly.

Usage:
    python3 check_queue.py

"""

import os
import sys

from database_helper import update_job_status, get_db, update_run_summary, get_protein_pathway
from settings_helper import get_max_cpus, get_max_gpus, find_between, get_amberti_path
from simulation_id_helper import get_complex_name, get_ligand_one, get_mode, get_run_name

lock_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'check_queue.lock')


def is_locked(lock_file):
    return os.path.exists(lock_file)


def acquire_lock(lock_file):
    with open(lock_file, 'w') as lock:
        lock.write(str(os.getpid()))


def release_lock(lock_file):
    os.remove(lock_file)


def get_transformations(unit_type, max_type):
    """
    Get a list of transformations to send based on unit type and maximum allowed.

    Parameters:
        unit_type (str): The unit type ('gpu' or 'cpu').
        max_type (int): Maximum allowed for the unit type.

    Returns:
        list: List of transformation IDs to send.
    """
    is_gpu = 1 if unit_type == 'gpu' else 0

    # Connect to the database
    db = get_db()
    cursor = db.cursor()

    # Get number of transformations sent or running
    cursor.execute(f"SELECT simulation_id FROM simulations WHERE gpu={is_gpu} and (job_status=1 or job_status=2)")
    transformations_sent_running = cursor.fetchall()
    type_sent_running = len(transformations_sent_running)

    # Calculate the number of transformations to send
    type_to_send = max_type - type_sent_running
    if type_to_send <= 0:
        return []

    # Get the transformations in the queue
    cursor.execute(f"SELECT simulation_id FROM simulations WHERE gpu={is_gpu} and job_status=0")

    # Get the transformations to send
    transformations_to_send = cursor.fetchall()[:type_to_send]
    transformations_to_send = [transformation[0] for transformation in transformations_to_send]
    return transformations_to_send


def generate_xpus(transformations_to_send):
    """
    Generate XPUs for a list of transformations.

    Parameters:
        transformations_to_send (list): List of simulation IDs to process.
    """
    for simulation_id in transformations_to_send:
        os.chdir(get_protein_pathway(get_run_name(simulation_id)))
        os.chdir(get_ligand_one(simulation_id))
        os.chdir(get_complex_name(simulation_id))

        complex_name = get_complex_name(simulation_id)
        mode = get_mode(simulation_id)

        print(os.getcwd())

        # Loads the parameters from the file
        timask1, timask2, scmask1, scmask2 = get_data_from_params(complex_name, simulation_id)
        update_job_status(1, simulation_id)
        os.system(
            f'python3 {os.path.join(get_amberti_path(), f"{mode}.py")} -c {complex_name} --timask1 {timask1}'
            f' --timask2 {timask2} --scmask1 {scmask1} --scmask2 {scmask2} -r {simulation_id}')


def get_data_from_params(complex_name, simulation_id):
    with open(f'params_{complex_name}.in', 'r') as f:
        data = f.read()
        timask1 = find_between(data, "timask1='", "'")
        timask2 = find_between(data, "timask2='", "'")
        scmask1 = find_between(data, "scmask1='", "'")
        scmask2 = find_between(data, "scmask2='", "'")

    for i in timask1, timask2, scmask1, scmask2:
        if i[0] != ':':
            update_job_status(4, simulation_id)
            sys.exit('ERROR: timask1, timask2, scmask1, scmask2 must start with :')

    return timask1, timask2, scmask1, scmask2


if __name__ == '__main__':
    if is_locked(lock_file_path):
        print("Another instance is already running. Exiting.")
    else:
        try:
            acquire_lock(lock_file_path)

            # Get and generate GPUs
            transformations_to_send = get_transformations('gpu', get_max_gpus())
            generate_xpus(transformations_to_send)

            # Get and generate CPUs
            transformations_to_send = get_transformations('cpu', get_max_cpus())
            generate_xpus(transformations_to_send)

            update_run_summary()

        finally:
            release_lock(lock_file_path)




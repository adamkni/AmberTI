"""When the simulation ends, this code is invoked to check whether there is any other simulation waiting to be called
and if there is one, it will send it into a row
Also will analyse the ended simulation

When the simulation starts changes the status of the simulation to running

When the simulation gives error changes the status of the simulation to error"""


import os
import argparse

from database_helper import update_job_status, insert_into_simulations
from settings_helper import get_amberti_path
from simulation_id_helper import get_updated_simulation_id

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script takes care of the queue of simulations after simulation '
                                                 'ends')
    parser.add_argument('-r', '--simulation_id', help="Simulation id")
    parser.add_argument('-s', '--status', help="Status of the simulation", required=True, type=int)

    args = parser.parse_args()
    simulation_id = args.simulation_id
    job_status = args.status

    # Updates job status in the database
    update_job_status(job_status, simulation_id)

    # If the simulation ends, it will check if there is any other follow-up simulation to be called
    if job_status == 3:
        if ('_all_' in simulation_id and '_4_' not in simulation_id) or (
                '_ti1_' in simulation_id and '_1_' in simulation_id) or (
                '_ti2_' in simulation_id and '_3_' in simulation_id):
            updated_sim_id = get_updated_simulation_id(simulation_id)
            is_gpu = 0 if '_2_' in updated_sim_id else 1
            insert_into_simulations(updated_sim_id, is_gpu)

    # If the simulation ends or gives error, it will check if there is any other simulation waiting to be called
    if job_status in (3, 4):
        os.system(f'python3 {os.path.join(get_amberti_path(), "check_queue.py")}')

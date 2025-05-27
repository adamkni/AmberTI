#!/bin/python3

"""Generates simulation IDs and adds them to the database
to be queued for execution."""

import argparse
import os

from database_helper import insert_into_simulations, create_run_summary, run_name_exists
from settings_helper import get_amberti_path


def get_all_lines_stripped(file):
    """Get all non-empty lines from a file.

    Parameters
    ----------
    file : str
        Path to input file.

    Returns
    -------
    list of str
        List of non-empty stripped lines.

    """
    with open(file, 'r') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines if line.strip()]
    return lines


def convert_lines_to_modes(lines, mode, run_name):
    """Convert ligand pairs into simulation IDs

    Parameters
    ----------
    lines : list of str
        List of ligand pairs.
    mode : str
        Simulation mode (ti1, ti2, etc.)
    run_name : str
        Name of the run.

    Returns
    -------
    list of str
        List of simulation IDs.

    """
    if mode in ('all', 'ti1', 'ti1p1'):
        simulation_ids = [line + "_1_" + mode + "_" + run_name for line in lines]
    elif mode == 'ti1p2':
        simulation_ids = [line + "_2_ti1p2_" + run_name for line in lines]
    elif mode in ('ti2p1', 'ti2'):
        simulation_ids = [line + "_3_" + mode + "_" + run_name for line in lines]
    elif mode == 'ti2p2':
        simulation_ids = [line + "_4_ti2p2_" + run_name for line in lines]
    else:
        print("Wrong mode")
        exit(1)
    return simulation_ids


def write_to_file(simulation_ids, mode, wat=False):
    """Write simulation IDs to the database.

    Parameters
    ----------
    simulation_ids : list of str
        List of simulation IDs to add.
    mode : str
        Simulation mode.

    """
    for simulation_id in simulation_ids:
        is_gpu = 0 if mode == 'ti1p2' else 1
        insert_into_simulations(simulation_id, is_gpu)
        if not wat:
            simulation_id_wat = simulation_id.split('_', 1)[0] + '-wat_' + simulation_id.split('_', 1)[1]
            insert_into_simulations(simulation_id_wat, is_gpu)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script gives input for ti1slow and ti2 scripts')
    parser.add_argument('-i', '--input', help="File with list of ligand combinations to run simulations at. "
                                              "Each ligand pair should be on a new line", required=True)
    parser.add_argument('-m', '--mode',
                        help="Mode of running the simulations.",
                        choices=['ti1p1', 'ti1p2', 'ti2p1', 'ti2p2', 'ti1', 'ti2', 'all'],
                        default='all')
    parser.add_argument('-n', '--run_name', help="Run name", required=True)
    parser.add_argument('--wat', help="Have water simulatoins in the file explicitly", action='store_true')
    parser.add_argument('-d', '--modification', help="Modification of the run", required=False)
    parser.add_argument('-p', '--protein', help="Protein name", required=True)

    args = parser.parse_args()
    mode = args.mode
    run_name = args.run_name
    modification = args.modification
    protein = args.protein

    # Check if the run name is already in the database and modification file exists and that the protein folder exists
    if run_name_exists(run_name):
        print("Run name already exists in the database")
        exit(1)
    if modification is not None and not os.path.isfile(modification):
        print("Modification file does not exist")
        exit(1)
    if not os.path.isdir(os.path.join(get_amberti_path(), protein)):
        print("Protein folder does not exist")
        exit(1)



    # Process input
    lines = get_all_lines_stripped(args.input)
    simulation_ids = convert_lines_to_modes(lines, mode, run_name)

    # Put simulation IDs into the database
    write_to_file(simulation_ids, mode, args.wat)

    # Write to the run_summary table
    create_run_summary(run_name, protein, modification)

    # Check the queue and run simulations
    os.system(f'python3 {os.path.join(get_amberti_path(), "check_queue.py")}')

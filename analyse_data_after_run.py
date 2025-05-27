""" Automates analysing data after run.

It performs the following tasks:

1. Saves the run information, including simulation details, to a database.
2. Executes an analysis workflow.
3. Calculates and stores the convergence of each lambda window and the total convergence of the simulation.
4. Records the lambdas and free energy values in the database.
5. Updates the error status in the run info to indicate errorlessness during analysis.

Usage:
    python script_name.py -r simulation_id [-k skiptime]

Arguments:
    -r, --simulation_id: Input file with ligands (required).
    -K, --skiptime: Skip some time at the beginning (default is '0').

Note: If the script does not run correctly, the error status in the run info will stay set to 1.
"""

import argparse
import os
import pandas as pd
import numpy as np
import sqlite3
import datetime

from alchemlyb.parsing.amber import extract_dHdl
from alchemlyb.preprocessing import decorrelate_dhdl, dhdl2series
from alchemlyb.convergence import fwdrev_cumavg_Rc

from database_helper import get_db, get_protein_pathway
from settings_helper import get_amberti_path
from simulation_id_helper import get_run_name, get_ligand_one, get_ligand_two, get_is_wat, get_complex_name, \
    get_result_id, get_run_name_from_result_id


def save_convergence(db, result_id, run_name):
    """
    Save the convergence of each lambda window and the total convergence of the simulation.

    Parameters
    ----------
    db : sqlite3.Connection
        Database connection.
    result_id : str
        Id of the simulation result.
    run_name : str
        Name of the run.
    """
    os.chdir(os.path.join(get_protein_pathway(run_name), get_ligand_one(result_id), get_complex_name(result_id)))
    convergences = np.empty(12, dtype=object)
    for i in range(0, 12):
        os.chdir(str(i))
        file = get_complex_name(result_id) + '_prod_' + run_name + f'_{i}' + '.out'
        dhdl = extract_dHdl(file, T=300)
        decorrelated = decorrelate_dhdl(dhdl, remove_burnin=True)
        R_c, running_average = fwdrev_cumavg_Rc(dhdl2series(decorrelated), tol=2)
        convergences[i] = R_c
        db.execute('''INSERT INTO convergences (result_id, lambda, convergence) VALUES (?, ?, ?)''',
                   (result_id, i, R_c))
        os.chdir('..')
    db.execute('''UPDATE free_energies SET total_convergence = ? WHERE result_id = ?''',
               (np.mean(convergences), result_id))
    db.commit()

    # TODO check for number of lambda windows


def save_run_info(db, simulation_id):
    """
    Save the run info to the database.

    Parameters
    ----------
    db : sqlite3.Connection
        Database connection.
    simulation_id : str
        Id of the simulation.
    """
    db.execute('''INSERT INTO run_info (result_id, run_name, simulation_datetime,  ligand_1, ligand_2, 
                  is_wat, error) VALUES (?, ?, ?, ?, ?, ?, ?)''',
               (get_result_id(simulation_id), get_run_name(simulation_id), datetime.datetime.now(),
                get_ligand_one(simulation_id), get_ligand_two(simulation_id), get_is_wat(simulation_id), 1))
    db.commit()


def save_lambdas(db, result_id):
    """
    Save the lambdas and the free energy to the database.

    Parameters
    ----------
    db : sqlite3.Connection
        Database connection.
    result_id : str
        Id of the results.
    """
    run_name = get_run_name_from_result_id(result_id)
    current_protein_pathway = get_protein_pathway(run_name)
    data = pd.read_csv(os.path.join(current_protein_pathway, get_ligand_one(result_id), get_complex_name(result_id),
                                    'results.csv'), sep=',')
    lambdas = data.iloc[:, 2]
    errors = data.iloc[:, 3]
    for i in range(0, 11):
        db.execute('''INSERT INTO lambdas (result_id, lambda, lambda_result, error) VALUES (?, ?, ?, ?)''',
                   (result_id, i, lambdas[i], errors[i]))
    db.execute('''INSERT INTO free_energies (result_id, total_free_energy, total_error) VALUES (?, ?, ?)''',
               (result_id, data.iloc[12].loc['TI'], data.iloc[12].loc['TI_Error']))
    db.commit()


def save_analysis_errorless(db, result_id):
    """
    Update the error status in the run info to indicate errorlessness.

    Parameters
    ----------
    db : sqlite3.Connection
        Database connection.
    result_id : str
        Id of the result.
    """
    db.execute('''UPDATE run_info SET error = 0 WHERE result_id = ?''', (result_id,))
    db.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script runs workflow for several ligands')
    parser.add_argument('-r', '--simulation_id', help='Input file with ligands', required=True)
    parser.add_argument('-k', '--skiptime', help='Skip some time at the beginning', default='0')
    parser.add_argument('--redo', help='Redo the analysis', action='store_true')

    args = parser.parse_args()
    simulation_id = args.simulation_id
    skip_time = args.skiptime

    complex = get_complex_name(simulation_id)
    result_id = get_result_id(simulation_id)
    run_name = get_run_name(simulation_id)

    db = get_db()
    if not args.redo:
        save_run_info(db, simulation_id)
    os.system(f'python3 {os.path.join(get_amberti_path(), "analysis_workflow.py")} -c {complex} -p _prod_{run_name} -s {skip_time}')
    save_lambdas(db, result_id)
    save_convergence(db, result_id, run_name)
    save_analysis_errorless(db, result_id)
    db.close()

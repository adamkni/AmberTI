#!/bin/python3

"""
db_helper.py

Helper functions for interacting with a SQLite database for storing
thermodynamic integration simulation data.

Functions
---------
get_db()
    Get a connection to the database.

add_job_id(job_id, simulation_id)
    Add a job ID for a simulation.

update_job_status(job_status, simulation_id)
    Update job status for a simulation.

insert_into_simulations(simulation_id, gpu)
    Insert a new simulation into the simulations table.

delete_simulation(simulation_id)
    Delete a simulation and associated result data.

delete_run(run_name)
    Delete all simulations and results with given run name.

delete_all_non_started_runs(run_name)
    Delete simulations with given run that have not started.

run_command(command)
    Run an SQL command on the database.

run_select_command(command)
    Run an SQL select command and print results.

get_simulation_errors()
    Get simulation IDs of jobs with errors.

redo_simulation(simulation_id)
    Reset simulation status to queue it again after error.

redo_error_simulation()
    Reset all simulations with errors to queue again.

get_analysis_errors()
    Get result IDs of analyses with errors.

delete_all_errors()
    Delete all simulations and results with errors.

get_energy_data(result_ids, db)
    Get free energy data for given result IDs.

make_averaged_energies(run_names, average_id)
    Average free energies over runs and save to database.

delete_all_data()
    Delete all data from all database tables.

cycle_averaged_data(combined_ids, cycle_id, ref_ligand, ref_value)
    Cycle average free energies and save cycled values.

transfer_databases(path_from_db, run_names)
    Transfer run data between databases.

"""
import os
import sqlite3
import pandas as pd
import numpy as np
import sys
import ast

from settings_helper import get_home_pathway, get_amberti_path
from simulation_id_helper import get_run_name, get_result_id, get_complex_name, get_ligand_one, \
    get_run_name_from_result_id


def get_db():
    """Get a connection to the SQLite database.

    Returns
    -------
    sqlite3.Connection
        Connection to the database at ti_simulations.db.

    """
    return sqlite3.connect(os.path.join(get_home_pathway(), 'ti_simulations.db'))


def add_job_id(job_id, simulation_id):
    """Add a job ID for a simulation.

    Associates a job ID with a simulation ID in the simulations table.

    Parameters
    ----------
    job_id : int
        The job ID to add.
    simulation_id : str
        The simulation ID to update.

    """
    db = get_db()
    db.execute(f"UPDATE simulations SET job_id={job_id}, job_status=1 WHERE simulation_id='{simulation_id}'")
    db.commit()
    db.close()


def update_job_status(job_status, simulation_id):
    """Update job status for a simulation.

    Sets the job status for a simulation in the simulations table.

    Parameters
    ----------
    job_status : int
        The job status code to set.
    simulation_id : str
        The simulation ID to update.

    """
    db = get_db()
    db.execute(f"UPDATE simulations SET job_status={job_status} WHERE simulation_id='{simulation_id}'")
    db.commit()
    db.close()


def insert_into_simulations(simulation_id, gpu):
    """Insert a new simulation into the simulations table.

    Adds a new row for a simulation.

    Parameters
    ----------
    simulation_id : str
        The ID of the simulation to insert.
    gpu : int
        Whether it runs on GPU (1) or CPU (0).

    """
    run_name = get_run_name(simulation_id)
    db = get_db()
    db.execute(f"INSERT INTO simulations (run_name, simulation_id, gpu) "
               f"VALUES ('{run_name}', '{simulation_id}' , {gpu})")
    db.commit()
    db.close()


def delete_simulation(simulation_id):
    """Delete a simulation and associated result data.

    Removes a simulation and linked data from the database.

    Parameters
    ----------
    simulation_id : str
        The simulation ID to delete.

    """
    db = get_db()
    db.execute(f"DELETE FROM simulations WHERE simulation_id='{simulation_id}'")
    result_id = get_result_id(simulation_id)
    db.execute(f"DELETE FROM lambdas  WHERE result_id='{result_id}'")
    db.execute(f"DELETE FROM free_energies WHERE result_id='{result_id}'")
    db.execute(f"DELETE FROM convergences WHERE result_id='{result_id}'")
    db.execute(f"DELETE FROM run_info WHERE result_id='{result_id}'")
    db.commit()
    db.close()


def delete_run(run_name):
    """Delete all simulations and results with given run name.

    Removes all data from the database associated with a run name.

    Parameters
    ----------
    run_name : str
        The run name to delete data for.

    """
    db = get_db()
    db.execute(f"DELETE FROM simulations WHERE run_name='{run_name}'")
    db.execute(f"DELETE FROM lambdas  WHERE SUBSTR(result_id, INSTR(result_id, '_') + 1) = '{run_name}'")
    db.execute(f"DELETE FROM free_energies WHERE SUBSTR(result_id, INSTR(result_id, '_') + 1) = '{run_name}'")
    db.execute(f"DELETE FROM convergences WHERE SUBSTR(result_id, INSTR(result_id, '_') + 1) = '{run_name}'")
    db.execute(f"DELETE FROM run_info WHERE run_name='{run_name}'")
    db.execute(f"DELETE FROM run_summary WHERE run_name='{run_name}'")
    db.commit()
    db.close()


def delete_all_non_started_runs(run_name):
    """Delete simulations with given run that have not started.

    Removes simulations with a run name that are still queued (job_status=0).

    Parameters
    ----------
    run_name : str
        The run name to check for non-started simulations.

    """
    db = get_db()
    db.execute(f"DELETE FROM simulations WHERE run_name='{run_name}' AND job_status=0")
    db.commit()
    db.close()


def run_command(command):
    """Run an SQL command on the database.

    Allows running arbitrary SQL commands.

    Parameters
    ----------
    command : str
        The SQL command to execute.

    """
    db = get_db()
    db.execute(command)
    db.commit()
    db.close()


def run_select_command(command, whole=False):
    """Run an SQL select command and print results.

    Runs a select query and prints the returned data.

    Parameters
    ----------
    command : str
        The SQL select command to run.

    Returns
    -------
    pd.DataFrame
        Dataframe containing the results of the select query.

    """
    db = get_db()
    result = pd.read_sql_query(command, db)
    db.close()
    if whole:
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
    print(result)
    return result


def get_simulation_errors():
    """Get simulation IDs of jobs with errors.

    Returns
    -------
    pd.DataFrame
        Dataframe containing simulation IDs with errors.

    """
    db = get_db()
    errors = pd.read_sql_query(f"SELECT simulation_id FROM simulations WHERE job_status=4", db)
    print(errors)
    db.close()
    return errors


def redo_simulation(simulation_id):
    """Reset simulation status to queue it again.

    Sets a simulation's job status back to 0 to retry.

    Parameters
    ----------
    simulation_id : str
        The ID of the simulation to reset.

    """
    db = get_db()
    db.execute(f"UPDATE simulations SET job_id=NULL WHERE simulation_id='{simulation_id}'")
    db.execute(f"UPDATE simulations SET job_status=0 WHERE simulation_id='{simulation_id}'")
    db.commit()
    db.close()
    print(f'Simulation {simulation_id} is sent back to the queue.')
    os.system(f'python3 {os.path.join(get_amberti_path(), "check_queue.py")}')


def redo_error_simulation():
    """Reset all simulations with errors to queue again.

    Sets all simulations with job status 4 back to 0 to retry.

    """
    db = get_db()
    db.execute(f"UPDATE simulations SET job_id=NULL WHERE job_status=4")
    db.execute(f"UPDATE simulations SET job_status=0 WHERE job_status=4")
    db.commit()
    db.close()
    print(f'All error simulations are sent back to the queue.')
    os.system(f'python3 {os.path.join(get_amberti_path(), "check_queue.py")}')


def check_if_job_id_null(simulation_id):
    """Check if job ID is null for a simulation.

    Returns
    -------
    bool
        True if job ID is null, False otherwise.

    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT job_id FROM simulations WHERE simulation_id='{simulation_id}'")
    job_id = cursor.fetchone()[0]
    db.close()
    return job_id is None


def get_analysis_errors():
    """Get and print result IDs of analyses with errors.

    Returns
    -------
    pd.DataFrame
        Dataframe containing result IDs with errors.

    """
    db = get_db()
    errors = pd.read_sql_query(f"SELECT result_id FROM run_info WHERE error=1", db)
    print(errors)
    db.close()
    return errors


def delete_all_errors():
    """Delete all simulations and results with errors.

    Removes any data from the database with job or analysis errors.

    """
    db = get_db()
    db.execute(f"DELETE FROM simulations WHERE job_status=4")
    db.execute(f"DELETE FROM lambdas WHERE result_id=(SELECT result_id FROM run_info WHERE error=1)")
    db.execute(f"DELETE FROM free_energies WHERE result_id=(SELECT result_id FROM run_info WHERE error=1)")
    db.execute(f"DELETE FROM convergences WHERE result_id=(SELECT result_id FROM run_info WHERE error=1)")
    db.execute(f"DELETE FROM run_info WHERE error=1")
    db.commit()
    db.close()


def redo_analysis(result_id):
    """Perform analysis again

    Parameters
    ----------
    result_id : str
        The ID of the result to redo analysis for.
    """
    simulation_id = result_id.split('_', 1)[0] + '_1_all_' + result_id.split('_', 1)[1]
    os.system(f'python3 {os.path.join(get_amberti_path(), "analyse_data_after_run.py")} -r {simulation_id} --redo')


def redo_error_analysis():
    """Runs all analysis with error again."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT result_id FROM run_info WHERE error=1")
    result_ids = [result_id[0] for result_id in cursor.fetchall()]
    db.commit()
    db.close()
    print(f'All error analyses are sent back to the queue:')
    for result_id in result_ids:
        os.chdir(os.path.join(get_protein_pathway(get_run_name_from_result_id(result_id)), get_ligand_one(result_id),
                              get_complex_name(result_id)))
        print('Redoing result: ' + result_id)
        redo_analysis(result_id)


def update_run_summary():
    '''
    Update the run summary table with the current number of simulations, finished simulations, and error simulations.
    '''
    # Get Runs that are still active
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT run_name FROM run_summary WHERE simulation_count != finished_count OR simulation_count == 0")
    runs = [run[0] for run in cursor.fetchall()]
    for run in runs:
        cursor.execute(f"SELECT COUNT(simulation_id) FROM simulations WHERE run_name='{run}'")
        simulation_count = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(simulation_id) FROM simulations WHERE run_name='{run}' AND job_status=3")
        finished_count = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(simulation_id) FROM simulations WHERE run_name='{run}' AND job_status=4")
        error_count = cursor.fetchone()[0]
        cursor.execute(
            f"UPDATE run_summary SET simulation_count={simulation_count}, finished_count={finished_count}, error_count={error_count} WHERE run_name='{run}'")

    db.commit()
    db.close()


def create_run_summary(run_name, protein_name, modification_file=None):
    '''
    Create a new entry in the run_summary table.

    Parameters
    ----------
    run_name : str
        The run name to create a summary for.
    protein_name : str
        The protein name for the run.
    modification_file : str
        The modification file for the run.
    '''
    db = get_db()
    db.execute(
        f"INSERT INTO run_summary (run_name, protein_name, simulation_count, finished_count, error_count, modification_file) "
        f"VALUES ('{run_name}', '{protein_name}', 0, 0, 0, '{modification_file}')")
    db.commit()
    db.close()


def get_protein_name(run_name):
    '''
    Get the protein name for a given run name.

    Parameters
    ----------
    run_name : str
        The run name to get the protein name for.

    Returns
    -------
    str
        The protein name.
    '''
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT protein_name FROM run_summary WHERE run_name='{run_name}'")
    protein_name = cursor.fetchone()[0]
    db.close()
    return protein_name


def get_protein_pathway(run_name):
    '''
    Get the pathway to the protein folder.

    Parameters
    ----------
    run_name : str
        The run name to get the protein pathway for.

    Returns
    -------
    str
        The pathway to the protein folder.

    '''
    return os.path.join(get_home_pathway(), get_protein_name(run_name))


def get_modification_file(run_name):
    '''
    Get the modification file for a given run name.

    Parameters
    ----------
    run_name : str
        The run name to get the modification file for.

    Returns
    -------
    str
        The modification file.
    '''
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT modification_file FROM run_summary WHERE run_name='{run_name}'")
    modification_file = cursor.fetchone()[0]
    db.close()

    if modification_file == 'None':
        modification_file = None

    return modification_file


def modify_run_input(run_name, run_input, run, run_section=None):
    '''
    Modify the run input based on the modification file.

    Parameters
    ----------
    run_name : str
        The run name to get the modification file for.
    run_input : str
        The run input to modify.
    run : str
        The run to modify.
    run_section : str
        The run section to modify.

    Returns
    -------
    str
        The modified run input.
    '''
    # Get the modification file and checks if there is any modification for the given run
    mod_file = get_modification_file(run_name)
    if mod_file is not None:
        mod_file = os.path.join(get_home_pathway(), mod_file)
        with open(mod_file, 'r') as infile:
            # Deleting spaces
            lines = [i.strip().replace(" ", "").strip() for i in infile.readlines()]

        # If no modification for the given run, return the original run input
        if run not in lines:
            return run_input
        # Getting the header for the modifications
        if run in ['ti1p1', 'ti1p2']:
            if run_section in lines:
                header = run_section
            else:
                return run_input
        else:
            header = run

        # Getting the section to modify
        header_index = lines.index(header)
        end_index = lines[header_index:].index('&end') + header_index
        current_section = lines[header_index+1:end_index]

        # Modifying the run input to delete spaces around the '=' sign
        run_input_lines = run_input.split('\n')
        run_input_lines = [f'{i.split("=")[0].rstrip()}={i.split("=",1)[1].strip()}' if "=" in i else i for i in
                           run_input_lines]
        end_run_input_lines = [idx for idx, s in enumerate(run_input_lines) if '&end' in s][0]
        first_text_line_before_end = [idx for idx, s in enumerate(run_input_lines[:end_run_input_lines]) if '=' in s][
            -1]

        # Get the correct number of leading spaces
        leading_spaces = len(run_input_lines[first_text_line_before_end]) - len(
            run_input_lines[first_text_line_before_end].lstrip())

        # Modifying the run input
        for line in current_section:
            item = line.split('=')[0]
            value = line.split('=', 1)[1]
            if f'{item}=' in '\t'.join(run_input_lines):
                if 'DELETE' in value:
                    index = [idx for idx, s in enumerate(run_input_lines) if f'{item}=' in s][0]
                    run_input_lines.pop(index)
                else:
                    index = [idx for idx, s in enumerate(run_input_lines) if f'{item}=' in s][0]
                    run_input_lines[index] = f'{run_input_lines[index].split("=")[0]}={value},'
            else:
                run_input_lines.insert(end_run_input_lines, f'{leading_spaces * " "}{item}={value},')
        run_input = '\n'.join(run_input_lines)

    return run_input


def run_name_exists(run_name):
    '''Check if run name exists in the database.

    Parameters
    ----------
    run_name : str
        The run name to check for.

    Returns
    -------
    bool
        True if run name exists, False otherwise.'''
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT COUNT(run_name) FROM run_summary WHERE run_name='{run_name}'")
    count = cursor.fetchone()[0]
    db.close()
    return count > 0


def get_energy_data(result_ids, db):
    """Get free energy data for given result IDs.

    Queries total free energy, error, and convergence data.

    Parameters
    ----------
    result_ids : list of str
        List of result IDs to get data for.
    db : sqlite3.Connection
        Database connection object.

    Returns
    -------
    pd.DataFrame
        DataFrame with energy data for the result IDs.

    """
    return pd.read_sql_query('''SELECT total_free_energy, total_error, total_convergence
                                                        FROM free_energies
                                                        WHERE result_id IN ({})'''.format(
        ','.join('?' * len(result_ids))), db, params=result_ids)


def make_averaged_energies(run_names, average_id):
    """Average free energies over runs and save to the database.

    Calculates forward and reverse averages for runs.
    Saves averaged values associated with an ID.

    Parameters
    ----------
    run_names : list of str
        List of run names to average.
    average_id : str
        ID to associate averaged values with.

    """

    # Check if run_names is a string and convert to list if needed
    if isinstance(run_names, str):
        if '[' in run_names:
            # make list from string
            run_names = ast.literal_eval(run_names)
        else:
            run_names = [run_names]

    # Connect to the SQLite database
    db = get_db()
    cursor = db.cursor()

    # Get unique ligand combinations for the run names
    combinations = pd.read_sql_query('''SELECT ligand_1, ligand_2
                      FROM run_info
                      WHERE run_name IN ({})'''.format(','.join('?' * len(run_names))), db, params=run_names)

    # Drop duplicate combinations
    unique_combinations = pd.DataFrame(np.sort(combinations, axis=1), columns=combinations.columns).drop_duplicates()

    # Loop through unique combinations
    for ligand_1, ligand_2 in unique_combinations[['ligand_1', 'ligand_2']].values:

        # Initialize variables to store forward/reverse averages
        free_energy = [None] * 4
        error = [None] * 4
        convergence = [None] * 4

        # Query free energies for the combination:
        # ligand_1, ligand_2, is_wat
        queries = [
            (ligand_1, ligand_2, 0),
            (ligand_1, ligand_2, 1),
            (ligand_2, ligand_1, 0),
            (ligand_2, ligand_1, 1)
        ]

        # Go through each query and calculate averages
        for i, query in enumerate(queries):

            # Get result IDs for the query
            cursor.execute(
                '''SELECT result_id FROM run_info WHERE ligand_1=? AND ligand_2=? AND is_wat=? AND run_name IN ({})'''.format(
                    ','.join('?' * len(run_names))), query + tuple(run_names))
            result_ids = cursor.fetchall()

            if len(result_ids) > 0:
                # Extract result IDs from list of tuples
                result_ids = [result_id[0] for result_id in result_ids]

                # Get free energy data for the result IDs
                free_energy_data = get_energy_data(result_ids, db)

                # Calculate averages
                free_energy[i] = free_energy_data['total_free_energy'].mean()
                error[i] = free_energy_data['total_error'].mean()
                convergence[i] = free_energy_data['total_convergence'].mean()

        # Calculate how many forward/reverse simulations have not been calculated
        forward_none_count = free_energy[:2].count(None)
        reverse_none_count = free_energy[2:].count(None)

        # If none ligand_1 to ligand_2 simulations have been calculated
        if forward_none_count == 2:
            forward_energy = forward_error = forward_convergence = None

        # If only one ligand_1 to ligand_2 simulation has been calculated
        elif forward_none_count == 1:
            # Raise exception
            raise Exception('Forward free energy calculation failed at ' + ligand_1 + '-' + ligand_2)

        # If both ligand_1 to ligand_2 simulations have been calculated
        elif forward_none_count == 0:

            # Calculate one edge of the cycle
            forward_energy = free_energy[0] - free_energy[1]
            forward_error = np.sqrt(error[0] ** 2 + error[1] ** 2)
            forward_convergence = (convergence[0] + convergence[1]) / 2

        if reverse_none_count == 2:
            reverse_energy = reverse_error = reverse_convergence = None
        elif reverse_none_count == 1:
            # Raise exception
            raise Exception('Reverse free energy calculation failed at ' + ligand_1 + '-' + ligand_2)
        elif reverse_none_count == 0:
            reverse_energy = free_energy[2] - free_energy[3]
            reverse_error = np.sqrt(error[2] ** 2 + error[3] ** 2)
            reverse_convergence = (convergence[2] + convergence[3]) / 2

        # Calculate final averaged values
        if forward_energy is not None and reverse_energy is not None:
            averaged_energy = (forward_energy - reverse_energy) / 2
            averaged_error = np.sqrt(forward_error ** 2 + reverse_error ** 2) / 2
            averaged_convergence = (forward_convergence + reverse_convergence) / 2

        # If only reverse, use reverse and negate
        elif forward_energy is None and reverse_energy is not None:
            averaged_energy = -reverse_energy
            averaged_error = reverse_error
            averaged_convergence = reverse_convergence

        # If only forward, use forward as average
        elif forward_energy is not None and reverse_energy is None:
            averaged_energy = forward_energy
            averaged_error = forward_error
            averaged_convergence = forward_convergence

        # If neither forward nor reverse, raise exception
        else:
            raise Exception('Both forward and reverse free energy calculations failed')

        # Insert averaged values into database
        db.execute('''INSERT INTO averaged_free_energies (comb_result_id, ligand_1, ligand_2, total_free_energy_averaged, total_error_averaged, total_convergence_averaged)
                        VALUES (?, ?, ?, ?, ?, ?)''', (
            ligand_1 + '-' + ligand_2 + '_' + average_id, ligand_1, ligand_2, averaged_energy, averaged_error,
            averaged_convergence))
        db.commit()


def delete_all_data():
    """Delete all data from all database tables."""
    db = get_db()
    tables = [
        "simulations",
        "lambdas",
        "free_energies",
        "convergences",
        "run_info",
        "averaged_free_energies",
        "cycle_closure",
        "run_summary"
    ]
    for table in tables:
        db.execute(f"DELETE FROM {table}")
    db.commit()
    db.close()


def cycle_averaged_data(averaging_ids, cycle_id, reference_ligand, reference_value):
    """Cycle average free energies and save cycled values.

        Uses an external Weighted_cc script to perform cycle closure on averages.
        Saves the cycled values back to the database.

        Parameters
        ----------
        averaging_ids : list of str
            List of combined result IDs to cycle.
        cycle_id : str
            ID to associate cycled values with.
        reference_ligand : str
            Ligand to use as reference for cycling.
        reference_value : float
            Binding energy of reference ligand to shift energies to.

        """
    if isinstance(averaging_ids, str):
        if '[' in averaging_ids:
            # make list from string
            averaging_ids = ast.literal_eval(averaging_ids)
        else:
            averaging_ids = [averaging_ids]

    db = get_db()
    all_data_to_cycle = pd.read_sql_query('''SELECT ligand_1, ligand_2, total_free_energy_averaged, total_error_averaged, total_convergence_averaged
                          FROM averaged_free_energies
                          WHERE SUBSTR(comb_result_id, INSTR(comb_result_id, '_') + 1) IN ({})'''.format(
        ','.join('?' * len(averaging_ids))), db, params=averaging_ids)

    # Make the DataFrame into csv file
    all_data_to_cycle.to_csv(os.path.join(get_home_pathway(), f'to_cycle_{cycle_id}.csv'), index=False,
                             sep=' ', header=False)
    os.system(
        f'python3 {os.path.join(os.path.dirname(os.path.realpath(__file__)), "Weighted_cc", "wcc_main.py")} -f {os.path.join(get_home_pathway(), f"to_cycle_{cycle_id}.csv")} -r {reference_ligand} -e {reference_value} -o {os.path.join(get_home_pathway(), f"cycled_{cycle_id}.csv")}')

    # Read the cycled data back into a DataFrame
    cycled_data = pd.read_csv(os.path.join(get_home_pathway(), f'cycled_{cycle_id}.csv'))

    # Remove the csv files
    os.remove(os.path.join(get_home_pathway(), f'to_cycle_{cycle_id}.csv'))

    # Save the cycled data to the database
    for i, row in cycled_data.iterrows():
        db.execute('''INSERT INTO cycle_closure (cycle_id, ligand, no_error, error, convergence_error)
                        VALUES (?, ?, ?, ?, ?)''', (
            cycle_id, row['Ligand'], row['Cycled_no_error'], row['Cycled_with_error1'], row['Cycled_with_error2']))
    db.commit()
    db.close()


def transfer_database(path_from_database, run_names):
    """Transfer run data between databases.

    Copies specified run data from one database to another.

    Parameters
    ----------
    path_from_database : str
        Path to database .db file to transfer from.
    run_names : list of str
        Names of runs to transfer.

    """
    # Makes a list out of string input
    if isinstance(run_names, str):
        if '[' in run_names:
            # make a list from string
            run_names = ast.literal_eval(run_names)
        else:
            run_names = [run_names]

    # Connect to both databases
    conn_source = sqlite3.connect(path_from_database)
    conn_destination = get_db()

    # Create cursors
    cursor_source = conn_source.cursor()
    cursor_destination = conn_destination.cursor()

    try:
        cursor_source.execute(
            'SELECT * FROM simulations WHERE run_name IN ({seq})'.format(seq=','.join(['?'] * len(run_names))),
            run_names)
        data_to_sync = cursor_source.fetchall()

        for row in data_to_sync:
            placeholders = ','.join(['?'] * len(row))
            query = f'INSERT INTO simulations VALUES ({placeholders})'
            cursor_destination.execute(query, row)

        # Synchronize data from run_info table where run_name is in run_names
        cursor_source.execute(
            'SELECT * FROM run_info WHERE run_name IN ({seq})'.format(seq=','.join(['?'] * len(run_names))),
            run_names)
        data_to_sync = cursor_source.fetchall()

        # Insert data into the destination database
        for row in data_to_sync:
            placeholders = ','.join(['?'] * len(row))
            query = f'INSERT INTO run_info VALUES ({placeholders})'
            cursor_destination.execute(query, row)

        # Get result_ids for the synchronized run_names
        result_ids = [row[0] for row in data_to_sync]

        # Synchronize data from lambdas, convergences, and free_energies tables where result_id is in result_ids
        tables_to_sync = ['lambdas', 'convergences', 'free_energies']
        for table_name in tables_to_sync:
            cursor_source.execute(
                f'SELECT * FROM {table_name} WHERE result_id IN ({{seq}})'.format(
                    seq=','.join(['?'] * len(result_ids))),
                result_ids)
            data_to_sync = cursor_source.fetchall()

            # Insert data into the destination database
            for row in data_to_sync:
                placeholders = ','.join(['?'] * len(row))
                query = f'INSERT INTO {table_name} VALUES ({placeholders})'
                cursor_destination.execute(query, row)

        # Commit the changes in the destination database
        conn_destination.commit()
    finally:
        # Close connections
        conn_source.close()
        conn_destination.close()

    # TODO move run_summary as well


if __name__ == '__main__':
    globals()[sys.argv[1]](*sys.argv[2:])

# TODO order and clean up and document the code

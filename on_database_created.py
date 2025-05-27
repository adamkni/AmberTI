"""Creates a database with all tables needed in it"""

import sqlite3
from settings_helper import get_home_pathway
import os


def update_tables(db):
    """Drop all existing tables in the database.

    Parameters
    ----------
    db : sqlite3.Connection
        Database connection object.

    """
    db.execute('''DROP TABLE IF EXISTS run_info''')
    db.execute('''DROP TABLE IF EXISTS lambdas''')
    db.execute('''DROP TABLE IF EXISTS free_energies''')
    db.execute('''DROP TABLE IF EXISTS averaged_free_energies''')
    db.execute('''DROP TABLE IF EXISTS cycle_closure''')
    db.execute('''DROP TABLE IF EXISTS simulations''')
    db.execute('''DROP TABLE IF EXISTS convergences''')
    db.execute('''DROP TABLE IF EXISTS run_summary''')


    # TODO find a way to update the tables without dropping them

def main():
    conn = sqlite3.connect(os.path.join(get_home_pathway(), 'ti_simulations.db'))
    """
    simulation_id - id of the simulation - consists of ligand transformation and run id
    run_name - name of the run - can be given to a great number of simulations
    job_id - id of the job in slurm
    job_status - 0 - in queue, 1 - sent, 2 - running, 3 - finished, 4 - error
    """

    update_tables(conn)
    conn.execute('''CREATE TABLE IF NOT EXISTS run_info
                    (result_id text PRIMARY KEY,
                    run_name text NOT NULL,
                    simulation_datetime datetime NOT NULL,
                    ligand_1 text NOT NULL,
                    ligand_2 text NOT NULL,
                    is_wat bool NOT NULL,
                    error bool NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS lambdas
                    (result_id text NOT NULL,
                    lambda int NOT NULL,
                    lambda_result float NOT NULL,
                    error float NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS convergences
                    (result_id text NOT NULL,
                    lambda int NOT NULL,
                    convergence float NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS free_energies
                    (result_id text NOT NULL,
                    total_free_energy float NOT NULL,
                    total_error float NOT NULL,
                    total_convergence float)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS averaged_free_energies
                    (comb_result_id text NOT NULL,
                    ligand_1 text NOT NULL,
                    ligand_2 text NOT NULL,
                    total_free_energy_averaged float NOT NULL,
                    total_error_averaged float NOT NULL,
                    total_convergence_averaged float)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS cycle_closure
                    (cycle_id text NOT NULL,
                    ligand text NOT NULL,
                    no_error float NOT NULL,
                    error float NOT NULL,
                    convergence_error float)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS simulations
                    (simulation_id text PRIMARY KEY,
                    run_name text NOT NULL,
                    job_id int,
                    job_status int DEFAULT 0,
                    gpu bool NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS run_summary
                    (run_name text PRIMARY KEY,
                    protein_name text NOT NULL,
                    simulation_count int NOT NULL,
                    error_count int NOT NULL,
                    finished_count int NOT NULL,
                    modification_file text)''')
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()


import sys
import textwrap

import on_database_created

sys.path.append('../')

import os
import unittest.mock
from unittest.mock import patch
import pytest
import sqlite3

from check_queue import get_transformations, generate_xpus, get_data_from_params
from database_helper import add_job_id, update_job_status, get_db, insert_into_simulations, delete_simulation, \
    delete_run, delete_all_data, delete_all_non_started_runs, run_command, run_select_command, make_averaged_energies, \
    cycle_averaged_data, redo_simulation, transfer_database, check_if_job_id_null, create_run_summary, get_protein_name, \
    modify_run_input, update_run_summary, get_modification_file
from run_several_sims import get_all_lines_stripped, convert_lines_to_modes, write_to_file
from simulation_id_helper import get_complex_name, get_ligand_one, get_ligand_two, get_is_wat, get_mode, get_run_name, \
    get_result_id, get_run_name_from_result_id
from settings_helper import get_gpu_settings, get_cpu_settings, get_home_pathway, get_environment, \
    get_max_cpus, get_max_gpus, set_settings_path, find_between
from analyse_data_after_run import save_lambdas, save_analysis_errorless, save_run_info
from simulation_id_helper import get_updated_simulation_id

gpu_settings = f'''#SBATCH --partition=compchemq
#SBATCH --qos=compchem
#SBATCH --account=compchem_acc
#SBATCH --mem=40g
#SBATCH -N1 --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --ntasks-per-socket=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=compchem001

module purge
module load amber-uon/cuda11/20bectgtx-eb-GCCcore-10.2.0'''

cpu_settings = f'''#SBATCH --partition=shortq
#SBATCH --mem=40g
#SBATCH -N1 --ntasks-per-node=1
#SBATCH --cpus-per-task=40
#SBATCH --ntasks-per-socket=1

module purge
module load amber-uon/intelmpi2019/20volta'''

home_pathway = 'C:/Users/knirs/PycharmProjects/amberti_clone/pytest'

environment = '''module load anaconda-uon/3
source activate alchem'''


# TODO make tests to work everywhere (not only on my computer)



class TestClass(unittest.TestCase):

    on_database_created.main()


    def test_get_transformations(self):
        lines = ['L21-L36_2_ti1p2_myid', 'L89-L44_2_ti1p2_some_id', 'L84-L36_2_ti1p2_joo', 'L89-L05_2_ti1p2_klo',
                 'L21-L39_2_ti1p2_klo',
                 'L89-L93_2_ti1p2_klo']
        mode = 'ti1p2'

        db = sqlite3.connect(os.path.join(home_pathway, 'ti_simulations.db'))
        db.execute('''DELETE FROM simulations''')
        db.commit()
        db.close()

        write_to_file(lines, mode)

        assert len(get_transformations('cpu', 3)) == 3
        add_job_id(4658, 'L89-L44_2_ti1p2_some_id')
        assert len(get_transformations('cpu', 3)) == 2

    def test_find_between(self):
        assert find_between('abc123def', 'abc', 'def') == '123'

    def test_get_all_lines(self):
        os.chdir(home_pathway)
        assert get_all_lines_stripped('test_running.temp') == ['1', '2', '3', '4', '5']

    def test_convert_lines_to_modes(self):
        assert convert_lines_to_modes(['1', '2', '3', '4', '5'], 'all', 'run1') == ['1_1_all_run1', '2_1_all_run1',
                                                                                    '3_1_all_run1', '4_1_all_run1',
                                                                                    '5_1_all_run1']
        assert convert_lines_to_modes(['1', '2', '3', '4', '5'], 'ti1p1', 'run_1') == ['1_1_ti1p1_run_1',
                                                                                       '2_1_ti1p1_run_1',
                                                                                       '3_1_ti1p1_run_1',
                                                                                       '4_1_ti1p1_run_1',
                                                                                       '5_1_ti1p1_run_1']
        assert convert_lines_to_modes(['1', '2', '3', '4', '5'], 'ti1p2', 'r6') == ['1_2_ti1p2_r6', '2_2_ti1p2_r6',
                                                                                    '3_2_ti1p2_r6',
                                                                                    '4_2_ti1p2_r6', '5_2_ti1p2_r6']
        assert convert_lines_to_modes(['1', '2', '3', '4', '5'], 'ti2p1', 'r6') == ['1_3_ti2p1_r6', '2_3_ti2p1_r6',
                                                                                    '3_3_ti2p1_r6', '4_3_ti2p1_r6',
                                                                                    '5_3_ti2p1_r6']

        lines = ['line1', 'line2']
        with pytest.raises(SystemExit):
            convert_lines_to_modes(lines, 'unknown_mode', 'id')

    def test_write_to_file(self):
        lines = ['L21-L36_2_ti1p2_12345', 'L89-L97_2_ti1p2_12345']
        mode = 'ti1p2'

        db = sqlite3.connect(os.path.join(home_pathway, 'ti_simulations.db'))
        db.execute('''DELETE FROM simulations''')
        db.commit()

        write_to_file(lines, mode)

        cursor = db.cursor()
        cursor.execute('''SELECT * FROM simulations''')
        results = cursor.fetchall()
        assert len(results) == 4
        assert ('L21-L36_2_ti1p2_12345', '12345', None, 0, 0) in results
        assert ('L21-L36-wat_2_ti1p2_12345', '12345', None, 0, 0) in results
        assert ('L89-L97-wat_2_ti1p2_12345', '12345', None, 0, 0) in results
        db.commit()
        db.close()

    def test_get_complex_name(self):
        assert get_complex_name('L21-L36_1_tip1p') == 'L21-L36'
        assert get_complex_name('L89-L97_2_ti2') == 'L89-L97'

    def assert_called_with_containing(self, mock, expected_substring):
        for call_args in mock.call_args_list:
            if expected_substring in call_args[0][0]:
                return
        raise AssertionError(f"Expected substring '{expected_substring}' not found in any call.")

    def test_generate_gpus(self):
        os.chdir(home_pathway)
        cwd = os.getcwd()
        transformations = ['L21-L36_1_ti1p1_myid', 'L89-L97_3_ti2p1_my_very_long_id', 'L21-L36_1_all_myid']
        with patch('os.system') as mock_os_system:
            generate_xpus(transformations)
            self.assert_called_with_containing(mock_os_system,
                                               f'ti1p1.py -c L21-L36 --timask1 :151 --timask2 :152 --scmask1 :151@S1,'
                                               f'CL4, --scmask2 :152@H1,N1,H, -r L21-L36_1_ti1p1_myid')
            self.assert_called_with_containing(mock_os_system,
                                               f'ti2p1.py -c L89-L97 --timask1 :151 --timask2 :152 --scmask1 :151@C1,H4,'
                                               f' --scmask2 :152@H1,N1,H, -r L89-L97_3_ti2p1_my_very_long_id')
            self.assert_called_with_containing(mock_os_system,
                                               f'ti1p1.py -c L21-L36 --timask1 :151 --timask2 :152 --scmask1 :151@S1,'
                                               f'CL4, --scmask2 :152@H1,N1,H, -r L21-L36_1_all_myid')
        os.chdir(cwd)

    def test_generate_cpus(self):
        os.chdir(home_pathway)
        cwd = os.getcwd()
        create_run_summary('myid', 'MCL1', None)
        create_run_summary('my_very_long_id', 'MCL1', None)
        transformations = ['L21-L36_2_ti1p2_myid', 'L89-L97_2_ti1p2_my_very_long_id']

        with patch('os.system') as mock_os_system:
            generate_xpus(transformations)
            assert mock_os_system.call_count == 2
            self.assert_called_with_containing(mock_os_system,
                                               'ti1p2.py -c L21-L36 --timask1 :151 --timask2 :152 --scmask1 :151@S1,CL4,'
                                               f' --scmask2 :152@H1,N1,H, -r L21-L36_2_ti1p2_myid')
            self.assert_called_with_containing(mock_os_system,
                                               'ti1p2.py -c L89-L97 --timask1 :151 --timask2 :152 --scmask1 :151@C1,H4,'
                                               f' --scmask2 :152@H1,N1,H, -r L89-L97_2_ti1p2_my_very_long_id')

        os.chdir(cwd)

    def test_wat_generate_xpus(self):
        os.chdir(home_pathway)
        cwd = os.getcwd()
        create_run_summary('myid', 'MCL1', None)
        create_run_summary('my_very_long_id', 'MCL1', None)
        transformations = ['L21-L36-wat_2_ti1p2_myid', 'L89-L97-wat_2_ti1p2_my_very_long_id']

        # Mocking the extract_complex_name and get_run_id functions
        with patch('os.system') as mock_os_system:
            generate_xpus(transformations)

            assert mock_os_system.call_count == 2
            self.assert_called_with_containing(mock_os_system,
                                               'ti1p2.py -c L21-L36-wat --timask1 :1 --timask2 :2 --scmask1 :1@S1,CL4,'
                                               f' --scmask2 :2@H1,N1,H, -r L21-L36-wat_2_ti1p2_myid')
            self.assert_called_with_containing(mock_os_system,
                                               'ti1p2.py -c L89-L97-wat --timask1 :1 --timask2 :2 --scmask1 :1@C1,H4,'
                                               f' --scmask2 :2@H1,N1,H, -r L89-L97-wat_2_ti1p2_my_very_long_id')

        transformations = ['L21-L36-wat_1_ti1p1_myid', 'L89-L97-wat_4_ti2p2_my_very_long_id']
        with patch('os.system') as mock_os_system:
            generate_xpus(transformations)
            self.assert_called_with_containing(mock_os_system,
                                               'ti1p1.py -c L21-L36-wat --timask1 :1 --timask2 :2 --scmask1 :1@S1,CL4,'
                                               f' --scmask2 :2@H1,N1,H, -r L21-L36-wat_1_ti1p1_myid')
            self.assert_called_with_containing(mock_os_system,
                                               'ti2p2.py -c L89-L97-wat --timask1 :1 --timask2 :2 --scmask1 :1@C1,H4,'
                                               f' --scmask2 :2@H1,N1,H, -r L89-L97-wat_4_ti2p2_my_very_long_id')
        os.chdir(cwd)

    def test_get_run_id(self):
        assert get_run_name('abc_def_ghi_jkl') == 'jkl'
        assert get_run_name('hello_world_to_jsem_ja') == 'jsem_ja'
        with pytest.raises(ValueError):
            get_run_name('no_underscores_here')

    def test_get_info_from_settings(self):
        os.chdir(get_home_pathway())
        set_settings_path(os.path.join(os.getcwd(), 'simulation_settings.in'))
        assert get_cpu_settings() == cpu_settings
        assert get_gpu_settings() == gpu_settings
        assert get_home_pathway() == home_pathway
        assert get_environment() == environment
        assert get_max_gpus() == 15
        assert get_max_cpus() == 14

    def test_simulation_id_helper(self):
        assert get_ligand_one('L21-L36_1_ti1p1_myid') == 'L21'
        assert get_ligand_two('L21-L36_1_ti1p1_myid') == 'L36'
        assert get_is_wat('L21-L36-wat_1_ti1p1_myid') == True
        assert get_is_wat('L21-L36_1_ti1p1_myid') == False
        assert get_mode('L21-L36_1_ti1p1_myid') == 'ti1p1'
        assert get_mode('L21-L36_2_ti1p1_myid') == 'ti1p2'
        assert get_mode('L21-L36_3_ti1p1_myid') == 'ti2p1'
        assert get_mode('L21-L36_4_ti1p1_myid') == 'ti2p2'
        with pytest.raises(ValueError):
            get_mode('L21-L36_5_ti1p1_myid')

    def test_get_data_from_params(self):
        os.chdir('MCL1/L21')
        os.chdir('L21-L36')
        assert get_data_from_params('L21-L36', 'L21-L36_1_all_id') == (':151', ':152', ':151@S1,CL4,', ':152@H1,N1,H,')
        os.chdir('..')

    def test_update_job_status(self):
        insert_into_simulations('L21-L36_1_ti1p1_myid', 0)
        update_job_status(2, 'L21-L36_1_ti1p1_myid')
        db = get_db()
        assert \
            db.execute(f"SELECT job_status FROM simulations WHERE simulation_id = 'L21-L36_1_ti1p1_myid'") \
                .fetchone()[0] == 2

    def test_get_updated_sim(self):
        assert get_updated_simulation_id('L21-L36_1_all_myid') == 'L21-L36_2_all_myid'
        assert get_updated_simulation_id('L21-L36_2_all_myid_very_long') == 'L21-L36_3_all_myid_very_long'
        assert get_updated_simulation_id('L21-L36-wat_3_all_myid') == 'L21-L36-wat_4_all_myid'

    def test_get_result_id(self):
        assert get_result_id('L21-L36_1_ti1p1_myid') == 'L21-L36_myid'
        assert get_result_id('L21-L36_2_all_myid') == 'L21-L36_myid'
        assert get_result_id('L21-L36-wat_3_all_myid_very_long') == 'L21-L36-wat_myid_very_long'

    def test_save_run_info(self):
        delete_all_data()
        db = get_db()
        save_run_info(db, 'L21-L36_4_all_myid')
        results = db.execute(f"SELECT * FROM run_info WHERE result_id = 'L21-L36_myid'").fetchone()[0]
        assert 'L21' in results
        assert 'L36' in results
        assert 'myid' in results
        assert db.execute(f"SELECT error FROM run_info WHERE result_id = 'L21-L36_myid'").fetchone()[0] == 1

    def test_save_lambdas(self):
        delete_all_data()
        create_run_summary('myid', 'MCL1', None)
        db = get_db()
        save_lambdas(db, 'L89-L97_myid')
        assert \
            db.execute(f"SELECT lambda_result FROM lambdas WHERE result_id = 'L89-L97_myid' and lambda = 1").fetchone()[
                0] == -7.045522
        assert db.execute(f"SELECT error FROM lambdas WHERE result_id = 'L89-L97_myid' and lambda = 5").fetchone()[
                   0] == 0.046385
        assert db.execute(f"SELECT total_free_energy FROM free_energies WHERE result_id = 'L89-L97_myid'").fetchone()[
                   0] == -97.082224
        assert db.execute(f"SELECT total_error FROM free_energies WHERE result_id = 'L89-L97_myid'").fetchone()[
                   0] == 0.139974

    def test_save_analysis_errorless(self):
        db = get_db()
        db.execute('''DELETE FROM run_info''')
        save_run_info(db, 'L21-L36_4_all_myid')
        save_analysis_errorless(db, 'L21-L36_myid')
        assert db.execute(f"SELECT error FROM run_info WHERE result_id = 'L21-L36_myid'").fetchone()[0] == 0

    def test_delete_simulations(self):
        delete_all_data()
        db = get_db()
        # insert data into all tables
        db.execute(
            '''INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ('L21-L36_4_all_myid', 0, 1, 'myid')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L21-L36_myid', 0, '2020-01-01 00:00:00', 'L21', 'L36', 0, 'myid')''')
        db.execute(
            '''INSERT INTO lambdas (result_id, lambda, lambda_result, error) VALUES ('L21-L36_myid', 1, -7.045522, 0.046385)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error) VALUES ('L21-L36_myid', -97.082224, 0.139974)''')
        db.execute('''INSERT INTO convergences (result_id, lambda, convergence) VALUES ('L21-L36_myid', 2, 0.087)''')
        db.execute('''INSERT INTO convergences (result_id, lambda, convergence) VALUES ('L21-L36_myid', 1, 0.046385)''')
        db.commit()
        assert db.execute("SELECT * FROM simulations").fetchall() != []
        assert db.execute("SELECT * FROM lambdas").fetchall() != []

        delete_simulation('L21-L36_4_all_myid')

        assert db.execute(f"SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM lambdas WHERE result_id='L21-L36_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM free_energies WHERE result_id='L21-L36_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM convergences WHERE result_id='L21-L36_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM run_info WHERE result_id='L21-L36_myid'").fetchall() == []

    def test_delete_run(self):
        delete_all_data()
        db = get_db()
        # insert data into all tables
        db.execute(
            '''INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ('L21-L36_4_all_myid', 0, 1, 'myid')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L21-L36_myid', 0, '2020-01-01 00:00:00', 'L21', 'L36', 0, 'myid')''')
        db.execute(
            '''INSERT INTO lambdas (result_id, lambda, lambda_result, error) VALUES ('L21-L36_myid', 1, -7.045522, 0.046385)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error) VALUES ('L21-L36_myid', -97.082224, 0.139974)''')
        db.execute('''INSERT INTO convergences (result_id, lambda, convergence) VALUES ('L21-L36_myid', 2, 0.087)''')
        db.execute('''INSERT INTO convergences (result_id, lambda, convergence) VALUES ('L21-L36_myid', 1, 0.046385)''')
        db.execute(
            '''INSERT INTO convergences (result_id, lambda, convergence) VALUES ('L21-L36_myidmyid', 1, 0.046385)''')
        db.execute(
            '''INSERT INTO convergences (result_id, lambda, convergence) VALUES ('L21-L36_myid_myid', 1, 0.046385)''')
        db.execute(
            '''INSERT INTO convergences (result_id, lambda, convergence) VALUES ('L21-L36-wat_myid_myid', 1, 0.046385)''')
        db.commit()
        assert db.execute("SELECT * FROM simulations").fetchall() != []
        assert db.execute("SELECT * FROM lambdas").fetchall() != []

        delete_run('myid')

        assert db.execute(f"SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM lambdas WHERE result_id='L21-L36_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM free_energies WHERE result_id='L21-L36_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM convergences WHERE result_id='L21-L36_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM run_info WHERE result_id='L21-L36_myid'").fetchall() == []
        assert db.execute(f"SELECT * FROM convergences WHERE result_id='L21-L36_myidmyid'").fetchall() != []
        assert db.execute(f"SELECT * FROM convergences WHERE result_id='L21-L36_myid_myid'").fetchall() != []
        assert db.execute(f"SELECT * FROM convergences WHERE result_id='L21-L36-wat_myid_myid'").fetchall() != []

    def test_delete_all_non_started_runs(self):
        delete_all_data()
        # create some non started and some started runs in simulations table
        db = get_db()
        db.execute(
            '''INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ('L21-L36_4_all_myid', 0, 1, 'myid')''')
        db.execute(
            '''INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ('L21-L36_4_all_myid2', 1, 1, 'myid2')''')
        db.execute(
            '''INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ('L21-L36_4_all_myid3', 0, 1, 'myid3')''')
        db.commit()

        delete_all_non_started_runs('myid')

        # check that only non started runs are deleted
        assert len(db.execute("SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid'").fetchall()) == 0
        assert len(db.execute(
            "SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid' and job_status=0").fetchall()) == 0
        assert db.execute("SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid2'").fetchall() != []
        assert db.execute("SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid3'").fetchall() != []

    def test_run_command(self):
        # create some random commands to run in 'run_command' function and then test they were done
        delete_all_data()
        db = get_db()
        run_command(
            '''INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ('L21-L36_4_all_myid', 0, 1, 'myid')''')
        run_command(
            '''INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ('L21-L36_4_all_myid2', 1, 1, 'myid2')''')

        assert len(db.execute("SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid'").fetchall()) == 1
        assert len(db.execute(
            "SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid2' and job_status=0").fetchall()) == 0

        run_select_command('''SELECT * FROM simulations WHERE simulation_id='L21-L36_4_all_myid' ''')

    def test_make_averaged_energies(self):
        delete_all_data()
        db = get_db()
        # create data to be averaged in run_info table and free_energies table
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L21-L36_myid', 0, '2020-01-01 00:00:00', 'L21', 'L36', 0, 'myid')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L21-L36-wat_myid', 0, '2020-01-01 00:00:00', 'L21', 'L36', 1, 'myid')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L36-L21_myid', 0, '2020-01-01 00:00:00', 'L36', 'L21', 0, 'myid')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L36-L21-wat_myid', 0, '2020-01-01 00:00:00', 'L36', 'L21', 1, 'myid')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L48-L87_myid', 0, '2020-01-01 00:00:00', 'L48', 'L87', 0, 'myid')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L48-L87_myid2', 0, '2020-01-01 00:00:00', 'L48', 'L87', 0, 'myid2')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L48-L87-wat_myid2', 0, '2020-01-01 00:00:00', 'L48', 'L87', 1, 'myid2')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L87-L48_myid2', 0, '2020-01-01 00:00:00', 'L87', 'L48', 0, 'myid2')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L87-L48-wat_myid2', 0, '2020-01-01 00:00:00', 'L87', 'L48', 1, 'myid2')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L87-L98_myid2', 0, '2020-01-01 00:00:00', 'L87', 'L98', 0, 'myid2')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L87-L98-wat_myid2', 0, '2020-01-01 00:00:00', 'L87', 'L98', 1, 'myid2')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L87-L48_myid4', 0, '2020-01-01 00:00:00', 'L87', 'L48', 0, 'myid4')''')
        db.execute(
            '''INSERT INTO run_info (result_id, error, simulation_datetime, ligand_1, ligand_2, is_wat, run_name) VALUES ('L87-L48-wat_myid4', 0, '2020-01-01 00:00:00', 'L87', 'L48', 1, 'myid4')''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L21-L36_myid', 10.10, 0.45, 0.1 )''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L21-L36-wat_myid', 5.5, 0.85, 0.25)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L36-L21_myid', 0.85, 0.4, 0)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L36-L21-wat_myid', 1.85, 0.44, 1)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L48-L87_myid', 0.88, 0.5, 0.45)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L48-L87_myid2', 0.98, 0.54, 0.6)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L48-L87-wat_myid2', 1.5, 0.45, 0.25)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L87-L48_myid2', 0.85, 0.4, 0.6)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L87-L48-wat_myid2', 1.95, 0.44, 1)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L87-L98_myid2', 0.95, 0.4, 0.4)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L87-L98-wat_myid2', 1.75, 0.54, 1)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L87-L48_myid4', 85.5, 0.4, 0.6)''')
        db.execute(
            '''INSERT INTO free_energies (result_id, total_free_energy, total_error, total_convergence) VALUES ('L87-L48-wat_myid4', 1.95, 0.44, 1)''')
        db.commit()

        make_averaged_energies(['myid', 'myid2'], 'aveid')

        # check that the data was averaged correctly

        assert db.execute(
            "SELECT total_free_energy_averaged FROM averaged_free_energies WHERE comb_result_id='L21-L36_aveid'").fetchone()[
                   0] == 2.8
        assert db.execute(
            "SELECT total_error_averaged FROM averaged_free_energies WHERE comb_result_id='L21-L36_aveid'").fetchone()[
                   0] > 0.565
        assert db.execute(
            "SELECT total_error_averaged FROM averaged_free_energies WHERE comb_result_id='L21-L36_aveid'").fetchone()[
                   0] < 0.566
        assert db.execute(
            "SELECT total_convergence_averaged FROM averaged_free_energies WHERE comb_result_id='L21-L36_aveid'").fetchone()[
                   0] == 0.3375

    def test_cycle_data(self):
        # test that the data is cycled correctly
        delete_all_data()
        db = get_db()
        db.execute(
            " INSERT INTO averaged_free_energies (comb_result_id, ligand_1, ligand_2, total_free_energy_averaged, total_error_averaged, total_convergence_averaged) VALUES ('L21-L36_aveid', 'L21', 'L36', 2.8, 0.565, 0.3375)")
        db.execute(
            " INSERT INTO averaged_free_energies (comb_result_id, ligand_1, ligand_2, total_free_energy_averaged, total_error_averaged, total_convergence_averaged) VALUES ('L36-L45_aveid', 'L36', 'L45', 0.85, 0.44, 0.5)")
        db.execute(
            " INSERT INTO averaged_free_energies (comb_result_id, ligand_1, ligand_2, total_free_energy_averaged, total_error_averaged, total_convergence_averaged) VALUES ('L45-L21_aveid1', 'L45', 'L21', 0.88, 0.5, 0.45)")
        db.execute(
            " INSERT INTO averaged_free_energies (comb_result_id, ligand_1, ligand_2, total_free_energy_averaged, total_error_averaged, total_convergence_averaged) VALUES ('L21-L58_aveid', 'L21', 'L58', 1.85, 0.44, 1)")
        db.execute(
            " INSERT INTO averaged_free_energies (comb_result_id, ligand_1, ligand_2, total_free_energy_averaged, total_error_averaged, total_convergence_averaged) VALUES ('L58-L36_aveid1', 'L58', 'L36', 0.95, 0.4, 0.4)")
        db.commit()

        cycle_averaged_data(['aveid', 'aveid1'], 'cycleid', 'L21', -5)

        assert len(db.execute("SELECT * from cycle_closure").fetchall()) == 4
        assert db.execute("SELECT error from cycle_closure WHERE cycle_id='cycleid' and ligand = 'L45'").fetchone()[
                   0] < -4

    def test_redo_simulation(self):
        delete_all_data()
        insert_into_simulations('L21-L36_1_ti1p1_redo_test', 0)
        create_run_summary('redo_test', 'MCL1')
        update_job_status(4, 'L21-L36_1_ti1p1_redo_test')
        redo_simulation('L21-L36_1_ti1p1_redo_test')
        db = get_db()
        assert db.execute(
            f"SELECT job_status FROM simulations WHERE simulation_id = 'L21-L36_1_ti1p1_redo_test'").fetchone()[0] == 1


    def test_synchronize_database(self):
        # Create a temporary source database with sample data
        table_data = {
            'run_info': [('23-24_run1', 'run1', '20.5.2012', 23, 24, 0, 0),
                         ('23-25_run1', 'run1', '20.5.2012', 23, 25, 0, 0),
                         ('13-24_run2', 'run2', '20.5.2012', 13, 24, 0, 0),
                         ('23-26_run3', 'run3', '20.5.2012', 23, 26, 1, 0)],
            'lambdas': [('23-24_run1', 0, 0.1, 0.5), ('23-24_run1', 0, 0.9, 0.2), ('23-24_run1', 2, 0.6, 0.4),
                        ('23-25_run1', 6, 0.1, 0.9), ('23-24_run1', 8, 0.1, 0.8), ('13-24_run2', 8, 0.1, 0.8),
                        ('13-24_run2', 10, 0.78, 0.8), ('23-26_run3', 1, 0.78, 0.8)],
            'convergences': [('23-24_run1', 1, 0.01), ('23-25_run1', 2, 0.02), ('13-24_run2', 3, 0.03),
                             ('23-26_run3', 3, 0.03)],
            'free_energies': [('23-24_run1', -0.009, 0.1, 0.5), ('23-24_run1', 2.2, 0.6, 0.4),
                              ('23-25_run1', 6.56, 0.1, 0.9), ('23-24_run1', 8.56, 0.1, 0.8),
                              ('13-24_run2', -8.48, 0.1, 0.8), ('13-24_run2', -10.5, 0.78, 0.8),
                              ('23-26_run3', 11.8, 0.78, 0.8)],
            'simulations': [('23-24_1_all_run1','run1', None, 1, 0), ('23-25_1_all_run1', 'run1', None, 3, 1)]
        }
        source_db_path = os.path.join(os.getcwd(), 'source_database.db')
        conn = sqlite3.connect(source_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS run_info
                            (result_id text PRIMARY KEY,
                            run_name text NOT NULL,
                            simulation_datetime datetime NOT NULL,
                            ligand_1 text NOT NULL,
                            ligand_2 text NOT NULL,
                            is_wat bool NOT NULL,
                            error bool NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS lambdas
                            (result_id text NOT NULL,
                            lambda int NOT NULL,
                            lambda_result float NOT NULL,
                            error float NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS convergences
                            (result_id text NOT NULL,
                            lambda int NOT NULL,
                            convergence float NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS free_energies
                            (result_id text NOT NULL,
                            total_free_energy float NOT NULL,
                            total_error float NOT NULL,
                            total_convergence float)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS simulations
                            (simulation_id text PRIMARY KEY,
                            run_name text NOT NULL,
                            job_id text,
                            gpu int NOT NULL,
                            job_status int NOT NULL)''')

            for table_name, data in table_data.items():
                num_columns = len(data[0])
                insert_sql = f'INSERT INTO {table_name} VALUES ({",".join(["?"] * num_columns)})'
                cursor.executemany(insert_sql, data)
            conn.commit()

            delete_all_data()
            # Call the synchronization function with sample data
            run_names_to_sync = ['run1', 'run3']
            transfer_database(source_db_path, run_names_to_sync)

            # Connect to the destination database to check if data was synchronized
            conn_destination = get_db()
            cursor_destination = conn_destination.cursor()

            try:
                # Verify that data from the 'run_info' table was synchronized
                cursor_destination.execute("SELECT * FROM run_info")
                synchronized_data = cursor_destination.fetchall()

                self.assertEqual(len(synchronized_data), 3)  # Check if two rows were synchronized

                # Verify that data from the other tables was synchronized
                for table_name, synchronizations in [('lambdas', 6), ('convergences', 3), ('free_energies', 5)]:
                    cursor_destination.execute(f"SELECT * FROM {table_name}")
                    synchronized_data = cursor_destination.fetchall()

                    self.assertEqual(len(synchronized_data), synchronizations)  # Check if two rows were synchronized

            finally:
                # Close connections and remove temporary files
                conn_destination.close()
        finally:
            conn.close()
            os.remove(source_db_path)


    def test_if_job_id_is_null(self):
        insert_into_simulations('L21-L36_1_ti1p1_redo_test', 0)
        insert_into_simulations('L21-L36_1_ti1p1_redo_test2', 1)
        add_job_id('123', 'L21-L36_1_ti1p1_redo_test')
        assert check_if_job_id_null('L21-L36_1_ti1p1_redo_test') == False
        assert check_if_job_id_null('L21-L36_1_ti1p1_redo_test2') == True
        redo_simulation('L21-L36_1_ti1p1_redo_test')
        assert check_if_job_id_null('L21-L36_1_ti1p1_redo_test') == True

    def test_get_run_name_from_result_id(self):
        assert get_run_name_from_result_id('L21-L36_redo_test') == 'redo_test'
        assert get_run_name_from_result_id('L21-L36-wat_redo_test2') == 'redo_test2'
        assert get_run_name_from_result_id('L21-L8998-wat_redo') == 'redo'
        assert get_run_name_from_result_id('L21-L36_redo_test_long_very') == 'redo_test_long_very'

    def test_get_protein_name(self):
        delete_all_data()
        create_run_summary('my_id', 'MCL1', None)
        create_run_summary('my_id2', 'BACE', None)
        assert get_protein_name('my_id') == 'MCL1'
        assert get_protein_name('my_id2') == 'BACE'


    def test_modify_run_input(self):
        run1 = textwrap.dedent(f'''\
    NVT MD w/No position restraints and PME (sander)
     &cntrl
      imin=1,
      maxcyc=20000,
      ntmin=2,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
    
      cut    = 9.0,
      iwrap=1,
      nsnb   = 10,
    
      ioutfm=1,
      icfe = 1, 
      ifsc = 1,
      timask1=':L21',
      timask2=':L36',
      scmask1=':L21@H1,H2,',
      scmask2=':L36@J5,K6,J3,',
      clambda=0.5,
    
      ntr=1,
      restraintmask = '!(:WAT,NA,CL)',
      restraint_wt = 100.0
    
    &end
     &ewald
       skinnb=2,
       nfft1=96,
       nfft2=96,
       nfft3=96,
     /
    ''')
        correct_run1 = textwrap.dedent(f'''\
            NVT MD w/No position restraints and PME (sander)
             &cntrl
              imin=1,
              maxcyc=100,
              ntmin=2,
              ntpr   = 1000,
              ntwx   = 10000,
              ntwe   = 1000,

              cut=10.0,
              iwrap=2,
              nsnb   = 10,

              ioutfm=1,
              icfe = 1, 
              ifsc = 1,
              timask1=':L21',
              timask2=':L36',
              scmask1=':L21@H1,H2,',
              scmask2=':L36@J5,K6,J3,',
              clambda=0.5,

              ntr=1,
              restraintmask = '!(:WAT,NA,CL)',
              restraint_wt = 100.0

            &end
             &ewald
               skinnb=2,
               nfft1=96,
               nfft2=96,
               nfft3=96,
             /
            ''')
        create_run_summary('my_id', 'MCL1', 'mod_file.in')
        assert modify_run_input('my_id', run1, 'ti1p1', '01_min').replace(" ", "") == correct_run1.replace(" ", "")

        run2 = textwrap.dedent(f'''\
           NVT MD w/No position restraints and PME (sander)
            &cntrl
             imin=1,
             maxcyc=20000,
             ntmin=2,
             ntpr   = 1000,
             ntwx   = 10000,
             ntwe   = 1000,
             
           &end
            &ewald
              skinnb=2,
              nfft1=96,
              nfft2=96,
              nfft3=96,
            /
           ''')
        correct_run2 = textwrap.dedent(f'''\
           NVT MD w/No position restraints and PME (sander)
            &cntrl
             imin=1,
             maxcyc=100,
             ntmin=2,
             ntpr   = 1000,
             ntwx   = 10000,
             ntwe   = 1000,
             
             iwrap=2,
           &end
            &ewald
              skinnb=2,
              nfft1=96,
              nfft2=96,
              nfft3=96,
            /
           ''')
        assert modify_run_input('my_id', run2, 'ti1p1', '02_min').replace(" ", "") == correct_run2.replace(" ", "")
        correct_run3 = textwrap.dedent(f'''\
                   NVT MD w/No position restraints and PME (sander)
                    &cntrl
                     imin=1,
                     maxcyc=100,
                     ntmin=2,
                     ntpr   = 1000,
                     ntwe   = 1000,

                   &end
                    &ewald
                      skinnb=2,
                      nfft1=96,
                      nfft2=96,
                      nfft3=96,
                    /
                   ''')
        assert modify_run_input('my_id', run2, 'ti2p1').replace(" ", "") == correct_run3.replace(" ", "")


    def test_update_run_summary(self):
        delete_all_data()
        create_run_summary('my_id', 'MCL1', 'mod_file.in')
        db =  get_db()
        db.execute('INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ("L21-L36_1_ti1p1_my_id", 0, 1, "my_id")')
        db.execute(
            'INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ("L21-L36_2_ti1p1_my_id", 1, 1, "my_id")')
        db.execute(
            'INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ("L21-L38_1_ti1p1_my_id", 2, 1, "my_id")')
        db.execute(
            'INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ("L21-L40_1_ti1p1_my_id", 3, 1, "my_id")')
        db.commit()
        update_run_summary()
        assert db.execute('SELECT simulation_count FROM run_summary WHERE run_name="my_id"').fetchone()[0] == 4
        assert db.execute('SELECT error_count FROM run_summary WHERE run_name="my_id"').fetchone()[0] == 0
        assert db.execute('SELECT finished_count FROM run_summary WHERE run_name="my_id"').fetchone()[0] == 1
        db.execute(
            'INSERT INTO simulations (simulation_id, job_status, gpu, run_name) VALUES ("L21-L33_1_ti1p1_my_id", 4, 1, "my_id")')
        db.execute('UPDATE simulations SET job_status=3 WHERE simulation_id="L21-L36_1_ti1p1_my_id"')
        db.commit()
        update_run_summary()
        assert db.execute('SELECT simulation_count FROM run_summary WHERE run_name="my_id"').fetchone()[0] == 5
        assert db.execute('SELECT error_count FROM run_summary WHERE run_name="my_id"').fetchone()[0] == 1
        assert db.execute('SELECT finished_count FROM run_summary WHERE run_name="my_id"').fetchone()[0] == 2

    def test_no_modifications(self):
        delete_all_data()
        create_run_summary('my_id', 'MCL1', None)
        assert get_modification_file('my_id') is None


if __name__ == '__main__':
    globals()[sys.argv[1]](*sys.argv[2:])



# TODO organise the tests into classes
# TODO test on update_job_status.py, ti1/ti2

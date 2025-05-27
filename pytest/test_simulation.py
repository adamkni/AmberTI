import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings_helper import get_home_pathway


def test_doing_some_simulations():
    home_pathway = get_home_pathway()
    pytest_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = f'{home_pathway}/TEST/L23/L23-L27-wat'
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    os.system(f'cp -v {pytest_dir}/MCL1/L23/L23-L27-wat/* {home_pathway}/TEST/L23/L23-L27-wat/')

    # create an input file
    input_file = 'L23-L27-wat'
    with open(f'{pytest_dir}/input.in', 'w') as f:
        f.write(input_file)

    now = datetime.datetime.now()
    date_string = now.strftime("%Y%m%d%H%M%S")

    os.system(
        f'python3 {pytest_dir}/../run_several_sims.py -i {pytest_dir}/input.in --wat -m all -n test_{date_string} -p '
        f'TEST -d {pytest_dir}/test_mod_file.in')


if __name__ == '__main__':
    test_doing_some_simulations()

#!/bin/python3

import argparse
import os
import textwrap
from database_helper import add_job_id, check_if_job_id_null, modify_run_input
from settings_helper import get_gpu_settings, get_environment, get_amberti_path
from simulation_id_helper import get_run_name

if __name__ == '__main__':
    clambda_list = [0.00922, 0.04794, 0.11505, 0.20634, 0.31608, 0.43738, 0.56262, 0.68392, 0.79366, 0.88495, 0.95206,
                    0.99078]

    parser = argparse.ArgumentParser(description='This script runs TI')
    parser.add_argument('-c', '--complex', help='Name of complex', required=True)
    parser.add_argument('--timask1', help='timask1', required=True)
    parser.add_argument('--timask2', help='timask2', required=True)
    parser.add_argument('--scmask1', help='scmask1', required=True)
    parser.add_argument('--scmask2', help='scmask2', required=True)
    parser.add_argument('--start', help='Start from this lambda, works only in case of skipeq', default=0, required=False)
    parser.add_argument('--end', help='End at this lambda, works only in case of skipeq', default=len(clambda_list) - 1,
                        required=False)
    parser.add_argument('-r', '--simulation_id', help='Run id of the simulation', required=False, default="no_id")

    args = parser.parse_args()

    complex = args.complex
    timask1 = args.timask1
    timask2 = args.timask2
    scmask1 = args.scmask1
    scmask2 = args.scmask2
    start = int(args.start)
    end = int(args.end)
    length = end - start + 1

    gpu_setting = get_gpu_settings()
    environment = get_environment()
    run_name = get_run_name(args.simulation_id)

    for i in range(start, end + 1):

        dir = i
        clambda = clambda_list[i]
        os.chdir("%s" % (dir))
        string = textwrap.dedent(f'''\
        NVT MD w/No position restraints and PME (sander)
         &cntrl
          ntx    = 1,
          irest  = 0,
          ntpr   = 1000,
          ntwx   = 50000,
          ntwe   = 1000,
          ig     = -1,
          ntf    = 1,
          ntb    = 1,
          cut    = 9.0,
          iwrap  = 1,
          nsnb   = 10,
          nstlim = 715000,
          t      = 0.0,
          nscm   = 1000,
          dt     = 0.001,
          temp0  = 300.0,
          tempi  = 300.0,
          ntt    = 1,
          tautp  = 2.0,
          ntc    = 1,
          ioutfm=1, 
          ntwv=-1,
          ntave=1000,
          icfe = 1, 
          ifsc = 1,
          timask1='{timask1}',
          timask2='{timask2}',
          scmask1='{scmask1},',
          scmask2='{scmask2},',
          clambda={clambda},
        &end
    
         &ewald
           skinnb=2, 
           nfft1=96, 
           nfft2=96, 
           nfft3=96,
         /
    
        ''')

        string = modify_run_input(run_name, string, 'ti2p2')

        with open('%s_prod.in' % dir, 'w') as outfile:
            outfile.write(string)
        os.chdir('../')

    string = textwrap.dedent(f'''\
#!/bin/bash
#SBATCH --time=20:00:00
#SBATCH --job-name=ti2p2
{gpu_setting}

trap "python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 4; exit" ERR

python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 2 

for i in {{0..{len(clambda_list) - 1}}}
do
cd ${{i}}
pmemd.cuda -O -i ${{i}}_prod.in -c {complex}_equi_${{i}}.rst7 -p ../{complex}.parm7 -o {complex}_prod_{run_name}_${{i}}.out -r {complex}_prod_{run_name}_${{i}}.rst7 -x {complex}_prod_{run_name}_${{i}}.nc
cd ..
done

python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 3

{environment}
python3 {os.path.join(get_amberti_path(), "analyse_data_after_run.py")} -r {args.simulation_id}
''')

    with open('ti2p2.txt', 'w') as outfile:
        outfile.write(string)

    if check_if_job_id_null(args.simulation_id):
        output = os.popen(f'sbatch ti2p2.txt').read().strip()
        print(output)
        jobid = output.split()[-1]

        add_job_id(jobid, args.simulation_id)

        print('Normal termination')
    else:
        print("Job id already exists. Please delete the job id to run again.")

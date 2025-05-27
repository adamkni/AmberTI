#!/bin/python3

import argparse
import os
import textwrap

from database_helper import add_job_id, check_if_job_id_null, modify_run_input
from settings_helper import get_cpu_settings, get_amberti_path
from simulation_id_helper import get_run_name

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script runs TI')
    parser.add_argument('-c', '--complex', help='Name of complex', required=True)
    parser.add_argument('--timask1', help='timask1', required=True)
    parser.add_argument('--timask2', help='timask2', required=True)
    parser.add_argument('--scmask1', help='scmask1', required=True)
    parser.add_argument('--scmask2', help='scmask2', required=True)
    parser.add_argument('-r', '--simulation_id', help='Run id of the simulation', required=False, default="no_id")

    args = parser.parse_args()

    complex = args.complex
    timask1 = args.timask1
    timask2 = args.timask2
    scmask1 = args.scmask1
    scmask2 = args.scmask2

    cpu_setting = get_cpu_settings()
    run_name = get_run_name(args.simulation_id)

    ti_equi_7 = textwrap.dedent(f'''\
    NPT MD w/No position restraints and PME (sander)
     &cntrl
      ntx    = 5,
      irest  = 1,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
      ig     = -1,
    
      ntf    = 1,
      ntb    = 2,
      ntp = 1, 
      pres0 = 1.0, 
      taup = 2.0,
      gamma_ln = 2.0,
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      nstlim = 200000,
      t      = 0.0,
      nscm   = 1000,
      dt     = 0.001,
    
      temp0  = 300.0,
      tempi  = 300.0,
      ntt    = 3,
      tautp  = 2.0,
    
      ntc    = 1,
      iwrap=1, 
      ioutfm=1, 
      ntwv=-1,
      ntave=1000,
      icfe = 1, 
      ifsc = 1,
      timask1='{timask1}',
      timask2='{timask2}',
      scmask1='{scmask1},',
      scmask2='{scmask2},',
      clambda=0.5,
    
      ntr=1,
      restraintmask = '!(:WAT,NA,CL)',
      restraint_wt = 5.0,
    
    &end
     &ewald
       skinnb=2, 
       nfft1=96, 
       nfft2=96, 
       nfft3=96,
     /
     ''')

    ti_equi_7 = modify_run_input(run_name, ti_equi_7, 'ti1p2', '07_equi')

    with open('07_ti_equi.in', 'w') as outfile:
        outfile.write(ti_equi_7)

    ti_equi_8 = textwrap.dedent(f'''\
    NPT MD w/No position restraints and PME (sander)
     &cntrl
      ntx    = 5,
      irest  = 1,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
      ig     = -1,
    
      ntf    = 1,
      ntb    = 2,
      ntp = 1, 
      pres0 = 1.0, 
      taup = 2.0,
      gamma_ln = 2.0,
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      nstlim = 200000,
      t      = 0.0,
      nscm   = 1000,
      dt     = 0.001,
    
      temp0  = 300.0,
      tempi  = 300.0,
      ntt    = 3,
      tautp  = 2.0,
    
      ntc    = 1,
      iwrap=1, 
      ioutfm=1, 
      ntwv=-1,
      ntave=1000,
      icfe = 1, 
      ifsc = 1,
      timask1='{timask1}',
      timask2='{timask2}',
      scmask1='{scmask1},',
      scmask2='{scmask2},',
      clambda=0.5,
    
      ntr=1,
      restraintmask = '!(:WAT,NA,CL)',
      restraint_wt = 2.0,
    
    &end
     &ewald
       skinnb=2, 
       nfft1=96,
       nfft2=96,
       nfft3=96,
     /
     ''')

    ti_equi_8 = modify_run_input(run_name, ti_equi_8, 'ti1p2', '08_equi')

    with open('08_ti_equi.in', 'w') as outfile:
        outfile.write(ti_equi_8)

    ti_equi_9 = textwrap.dedent(f'''\
    NPT MD w/No position restraints and PME (sander)
     &cntrl
      ntx    = 5,
      irest  = 1,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
      ig     = -1,
    
      ntf    = 1,
      ntb    = 2,
      ntp = 1, 
      pres0 = 1.0, 
      taup = 2.0,
      gamma_ln = 2.0,
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      nstlim = 600000,
      t      = 0.0,
      nscm   = 1000,
      dt     = 0.001,
    
      temp0  = 300.0,
      tempi  = 300.0,
      ntt    = 3,
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
      clambda=0.5,
    
    &end
     &ewald
       skinnb=2, 
       nfft1=96, 
       nfft2=96, 
       nfft3=96,
     /
     ''')

    ti_equi_9 = modify_run_input(run_name, ti_equi_9, 'ti1p2', '09_equi')
    with open('09_ti_equi.in', 'w') as outfile:
        outfile.write(ti_equi_9)

    ti1p2_script = textwrap.dedent(f'''\
#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --job-name=ti1p2
{cpu_setting}

trap "python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 4; exit" ERR

python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 2

mpirun -np 40 pmemd.MPI -O -i 07_ti_equi.in -c {complex}_ti_heat.rst7 -p {complex}.parm7 -o {complex}_ti_equi1.out -r {complex}_ti_equi1.rst7 -x {complex}_ti_equi1.nc -ref {complex}_ti_heat.rst7
mpirun -np 40 pmemd.MPI -O -i 08_ti_equi.in -c {complex}_ti_equi1.rst7 -p {complex}.parm7 -o {complex}_ti_equi2.out -r {complex}_ti_equi2.rst7 -x {complex}_ti_equi2.nc -ref {complex}_ti_equi1.rst7
mpirun -np 40 pmemd.MPI -O -i 09_ti_equi.in -c {complex}_ti_equi2.rst7 -p {complex}.parm7 -o {complex}_ti_equi.out -r {complex}_ti_equi.rst7 -x {complex}_ti_equi.nc

python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 3
''')

    if check_if_job_id_null(args.simulation_id):
        with open('ti1p2.txt', 'w') as outfile:
            outfile.write(ti1p2_script)
        output = os.popen(f'sbatch ti1p2.txt').read().strip()
        print(output)
        jobid = output.split()[-1]

        add_job_id(job_id=jobid, simulation_id=args.simulation_id)
    else:
        print("Job id already exists. Please delete the job id to run again.")

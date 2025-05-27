#!/bin/python3

import argparse
import os
import textwrap

from database_helper import add_job_id, check_if_job_id_null, modify_run_input
from settings_helper import get_gpu_settings, get_amberti_path
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

    gpu_setting = get_gpu_settings()
    run_name = get_run_name(args.simulation_id)

    ti_min_1 = textwrap.dedent(f'''\
    NVT MD w/No position restraints and PME (sander)
     &cntrl
      imin=1,
      maxcyc=20000,
      ntmin=2,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
    
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      ioutfm=1,
      icfe = 1, 
      ifsc = 1,
      timask1='{timask1}',
      timask2='{timask2}',
      scmask1='{scmask1},',
      scmask2='{scmask2},',
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

    ti_min_1 = modify_run_input(run_name, ti_min_1, 'ti1p1', '01_min')

    with open('01_ti_min.in', 'w') as outfile:
        outfile.write(ti_min_1)

    ti_min_2 = textwrap.dedent(f'''\
    NVT MD w/No position restraints and PME (sander)
     &cntrl
      imin=1,
      maxcyc=20000,
      ntmin=2,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
    
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      ioutfm=1,
      icfe = 1, 
      ifsc = 1,
      timask1='{timask1}',
      timask2='{timask2}',
      scmask1='{scmask1},',
      scmask2='{scmask2},',
      clambda=0.5,
    
      ntr = 1,
      restraintmask = '!(:WAT,NA,CL) & !@H=',
      restraint_wt = 100.0
    
    &end
     &ewald
       skinnb=2, 
       nfft1=96, 
       nfft2=96, 
       nfft3=96,
     /
    ''')

    ti_min_2 = modify_run_input(run_name, ti_min_2, 'ti1p1', '02_min')

    with open('02_ti_min.in', 'w') as outfile:
        outfile.write(ti_min_2)

    ti_min_3 = textwrap.dedent(f'''\
    NVT MD w/No position restraints and PME (sander)
     &cntrl
      imin=1,
      maxcyc=20000,
      ntmin=2,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
    
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      ioutfm=1,
      icfe = 1, 
      ifsc = 1,
      timask1='{timask1}',
      timask2='{timask2}',
      scmask1='{scmask1},',
      scmask2='{scmask2},',
      clambda=0.5,
    
      ntr = 1,
      restraintmask = '@CA,C,O,N',
      restraint_wt = 100.0
    
    &end
     &ewald
       skinnb=2, 
       nfft1=96, 
       nfft2=96, 
       nfft3=96,
     /
    ''')

    ti_min_3 = modify_run_input(run_name, ti_min_3, 'ti1p1', '03_min')

    with open('03_ti_min.in', 'w') as outfile:
        outfile.write(ti_min_3)

    ti_min_4 = textwrap.dedent(f'''\
    NVT MD w/No position restraints and PME (sander)
     &cntrl
      imin=1,
      maxcyc=20000,
      ntmin=2,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
    
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      ioutfm=1,
      icfe = 1, 
      ifsc = 1,
      timask1='{timask1}',
      timask2='{timask2}',
      scmask1='{scmask1},',
      scmask2='{scmask2},',
      clambda=0.5,
    
      ntr = 1,
      restraintmask = '@CA,C,O',
      restraint_wt = 100.0
    
    &end
     &ewald
       skinnb=2, 
       nfft1=96, 
       nfft2=96, 
       nfft3=96,
     /
    ''')

    ti_min_4 = modify_run_input(run_name, ti_min_4, 'ti1p1', '04_min')

    with open('04_ti_min.in', 'w') as outfile:
        outfile.write(ti_min_4)

    ti_min_5 = textwrap.dedent(f'''\
    NVT MD w/No position restraints and PME (sander)
     &cntrl
      imin=1,
      maxcyc=20000,
      ntmin=2,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
    
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      ioutfm=1,
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

    ti_min_5 = modify_run_input(run_name, ti_min_5, 'ti1p1', '05_min')

    with open('05_ti_min.in', 'w') as outfile:
        outfile.write(ti_min_5)

    ti_heat_6 = textwrap.dedent(f'''\
    NVT MD w/No position restraints and PME (sander)
     &cntrl
      ntx    = 1,
      irest  = 0,
      ntpr   = 1000,
      ntwx   = 10000,
      ntwe   = 1000,
      ig     = -1,
    
      ntf    = 1,
      ntb    = 1,
      cut    = 9.0,
      iwrap  = 1,
      nsnb   = 10,
    
      nstlim = 1000000,
      t      = 0.0,
      nscm   = 1000,
      dt     = 0.001,
    
      temp0  = 300.0,
      tempi  = 0.0,
      ntt    = 3,
      gamma_ln = 2,
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
    
      nmropt=1,
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
    &wt 
        type='TEMP0', 
        istep1=0, 
        istep2=950000, 
        value1=0.0, 
        value2=300.0 
    /
    &wt 
        type='TEMP0', 
        istep1=950001, 
        istep2=1000000, 
        value1=300.0, 
        value2=300.0 
    /
    &wt type='END' /
    ''')

    ti_heat_6 = modify_run_input(run_name, ti_heat_6, 'ti1p1', '06_heat')

    with open('06_ti_heat.in', 'w') as outfile:
        outfile.write(ti_heat_6)

    ti1p1_script = textwrap.dedent(f'''\
#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --job-name=ti1p1
{gpu_setting}

trap "python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 4; exit" ERR

python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 2

pmemd.cuda -O -i 01_ti_min.in -c {complex}.rst7 -p {complex}.parm7 -o {complex}_ti_min1.out -r {complex}_ti_min1.rst7 -x {complex}_ti_min1.nc -ref {complex}.rst7
pmemd.cuda -O -i 02_ti_min.in -c {complex}_ti_min1.rst7 -p {complex}.parm7 -o {complex}_ti_min2.out -r {complex}_ti_min2.rst7 -x {complex}_ti_min2.nc -ref {complex}_ti_min1.rst7
pmemd.cuda -O -i 03_ti_min.in -c {complex}_ti_min2.rst7 -p {complex}.parm7 -o {complex}_ti_min3.out -r {complex}_ti_min3.rst7 -x {complex}_ti_min3.nc -ref {complex}_ti_min2.rst7
pmemd.cuda -O -i 04_ti_min.in -c {complex}_ti_min3.rst7 -p {complex}.parm7 -o {complex}_ti_min4.out -r {complex}_ti_min4.rst7 -x {complex}_ti_min4.nc -ref {complex}_ti_min3.rst7
pmemd.cuda -O -i 05_ti_min.in -c {complex}_ti_min4.rst7 -p {complex}.parm7 -o {complex}_ti_min5.out -r {complex}_ti_min5.rst7 -x {complex}_ti_min5.nc
pmemd.cuda -O -i 06_ti_heat.in -c {complex}_ti_min5.rst7 -p {complex}.parm7 -o {complex}_ti_heat.out -r {complex}_ti_heat.rst7 -x {complex}_ti_heat.nc -ref {complex}_ti_min5.rst7

python3 {os.path.join(get_amberti_path(), "update_job_status.py")} -r {args.simulation_id} -s 3
''')

    if check_if_job_id_null(args.simulation_id):
        with open('ti1p1.txt', 'w') as outfile:
            outfile.write(ti1p1_script)

        output = os.popen(f'sbatch ti1p1.txt').read().strip()
        print(output)
        jobid = output.split()[-1]

        add_job_id(job_id=jobid, simulation_id=args.simulation_id)
        print("Normal termination")
    else:
        print("Job id already exists. Please delete the job id to run again.")

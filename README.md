# Manual for TI in AMBER

## Prerequisites

All prerequisites are written in the _environment.yml_ file.

## 1 Setting up the environment

First, you need to set up the folder structure with all the files needed for the simulation.
You need to create a settings file that will include all important user-specific data. These include:
- **GPU_setting** - SBATCH settings for GPU cluster
- **CPU_setting** - SBATCH settings for CPU cluster
- **environment** - how to start an environment that includes alchemlyb and other packages
- **max_GPUs** - maximum number of jobs sent to GPU cluster at a time
- **max_CPUs** - maximum number of jobs sent to CPU cluster at a time
- **home_pathway** - complete path to the folder, that includes the amberti folder and all the
    transformation folders
- **current_protein** - name of the protein you are currently working with

Then, in the **home_pathway**, you have folders with the name of the proteins. 
Inside the protein folder, you have a folder for each ligand (ligand name cannot include a dash or underscore). 
Inside the ligand folder, you have a folder for each transformation (written as _ligand1-ligand2_). 
Example of such folder structure can be seen in the picture below.

In every transformation folder, you need to have the following files (e.g. for transformation _L23-L26_):

- L23-L26.rst
- L23-L26.parm
- params_L23-L26.in

The _params_L23-L26.in_ file contains masks to run the simulation, so that they can be automatically loaded to
run the simulations. 
Example of a text of such document would be:

```text
timask1=’:151’,
timask2=’:152’,
scmask1=’:151@CN1,CN2,CN3,CN4,HN1,HN2,HN3,HN4,HN5,HN6,HN7,HN8,’,
scmask2=’:152@H19,H22,’
```

There are some commands, you need to run before the first use: 

Following command saves the location of the settings file

```bash
python3 amberti/settings_helper.py set_settings_path "path" 
```

Following command creates the database where all data will be stored
```bash
python3 amberti/on_database_created.py
```
## 2 Running the simulations

To run the simulation, you need to run: 
```bash
python3 amberti/run_several_sims.py -i input_file -m mode -n run_name -p protein -d modification_file 
```
**Input_file** is a path to the input file with each transformation you
want to have on each row. It is not possible to put the same transformation several times.

If you want to distinguish between protein and water runs in the input file,
you can use **--wat** option.

**Mode** is what stage of simulation you want to run. The simulation is divided into 4 stages. 
The first two stages - _ti1p1_ and _ti1p2_ are general minimalisation and equilibration of the transformation. 
_Ti1p2_ is also the only CPU simulation. 
_Ti2p1_ is then the equilibration of all lambda states and _ti2p2_ is the production simulation.
If you want to run all the simulations from the beginning, you choose '_all_'. 
If you want to run either only first or second half, you can choose '_ti1_' or '_ti2_' respectively.

The **run_name** is a unique name for this run command, and you should only use every run_name once. 
It also helps to create a unique identifier of every simulation, and you will then be able to access the results of the
simulation by this identifier.

The **protein** is the name of the protein you are working with. 
All calculations will be made in the folder named as the protein.

The **modification_file** is an optional file that can be used to modify any of the simulations.
The structure of modification file can be seen in section 6.2.


## 3 Analysis of data

All data is analysed automatically at the end of each run. 
The next thing needed to do is to calculate the relative free energy from all the runs and
also to average any runs that were done in duplicates.
Therefore, you need to run the following command:

```bash
python3 database_helper.py make_averaged_energies "[run_name1, run_name2]" averaging_id 
```

Where **"\[run_name1, run_name2\]"** is list of all the run_names you want to
include in averaging and **averaging_id** is an identifier if you want to use this averaging
further.
To get absolute binding energy, you need to perform cycle closure with the following command:

```bash
python3 database_helper.py cycle_averaged_data "[averaging_id1, averaging_id2]" cycle_id reference_ligand reference_value 
```

- **"[averaging_id1, averaging_id2]"** is a list of averaging ids whose values will be used for cyclization
- **cycle_id** is an identifier of the cycle closure
- **reference ligand** is the ligand whose value will we use as a starting point for absolute binding energies
- **reference value** is binding energy of the reference ligand. 

The cyclisation results will be then stored both in database and in csv
file, and it will be also printed out. There are three columns. The first one (_cc_) uses uniform standard deviation. 
The second one (_wcc1_) uses errors to specify further the error, and the last one (_wcc2_) uses convergence for that. 

## 4 Documentation and helper methods

### 4.1 Database structure

You can easily access the database to retrieve any results you want. To get that, you need to
understand the structure of the database. There are several tables.

The first table is **run_summary**. It contains all the information about each run.

- **run_name** - name of the run assigned by user
- **protein** - name of the protein used in current simulation
- **simulation_count** - number of simulations in the run
- **error_count** - number of simulations that ended with an error
- **finished_count** - number of simulations that finished successfully
- **modification_file** - name of the file that contains the modification of runs (optional)

The **simulations** table takes care of all running simulations. **Simulation_id** is id unique to
the simulation. It has the following format: **proteinTransformation_currentPart_mode_runName**

- **ProteinTransformation** - ligands that are being transformed and addition _-wat_ if they
    are without protein e.g. L26-L85-wat
- **currentPart** - shows which part of the whole process is being done:
    - 1 - ti1p1
    - 2 - ti2p1
    - 3 - ti1p2
    - 4 - ti2p2
- **mode** - shows which part of the whole process need to be done - any of the previous or
    '_all_' to do all of them or _ti1/ti2_ to do only first/second half
- **runName** - name of the run assigned by user

Therefore, an example of a simulation_id would be _L26-L85-wat_1_ti1p1_run1_

**job_id** is the id of the job once, it is sent to sbatch.
**job_status** shows status of the job:

- **0** - waiting to be sent to the queue
- **1** - sent to the queue
- **2** - running
- **3** - done
- **4** - error


**gpu** shows true (=1) when the simulation is supposed to run on gpu cluster (ti1p1, ti2p1 and ti2p2
simulations)

In **run_info**, _simulation_id_ is exchanged into result_id that has format _proteinTransformation_runName_. 
It also includes when the simulation has ended and whether it was analysed
without any problems (_error_ - 0 means no error, 1 means error)

Then the next important one is **free_energies** table. 
It contains the results of every simulation, including _free_energy_, _error_ and _convergence_.
Then there is **averaged_free_energies** table, that allows us to make average of any runs
we have done by its _run_name_. Since we can make several of these using different _run_names_,
we are giving it separate id. Therefore, the _comb_result_id_ is _transformation_averagingId_
(e.g. L23-L26_MCL1_averaged).
The last table is **cycle_id**. Once again, we can use averages with several _averagingIds_, so
we are giving it a new id - _cycle_id_. It saves absolute free binding energy. And there will be
several values:

- **no_error** - does not use any error to make cycle closure
- **error** - uses error to make cycle closure
- **convergence_error** - uses convergence as an error during cycle closure

### 4.2 Database helper commands

The **database_helper.py** file contains several commands that can help looking at the database
and changing the results.

Each function in the **database_helper.py** file can be called in the following format:
```bash
python3 path/amberti/database_helper.py function_name arg1 arg2
```
If argument is a list then you would write it as _"\[arg1, arg2\]"_

The most versatile function is **run_command**. It takes one argument - an SQL command. 
If you want to run any SELECT SQL command, you cen use **select_run_command**.
You for example want to see all the simulations that finshed successfully. 
Then you would run:
```bash
python3 path/amberti/database_helper.py select_run_command "SELECT * FROM simulations WHERE job_status=3"
```

By default, it shows only some columns and also first and last few rows. 
If you want to see the whole table, add True at the end of the command.

If you want to delete certain simulation from all tables, you can use **delete_simulation(simulation_id)** function.

If you want to delete all simulations from all tables associated with certain run_name, 
you can use **delete_run(run_name)** function.

To delete all simulations from specific run_name that has not yet started, 
you can use **delete_all_non_started_runs(run_name)** function.

To find all simulations that have ended with an error,
you can run **get_simulation_errors** function.

To rerun a simulation, you can use **redo_simulation(simulation_id)** function.

To redo all simulations with error, you can use **redo_error_simulation** function.

To get errors that happened during analysis, you can use **get_analysis_errors** function.

To rerun analysis of a specific simulation, you can use **redo_analysis(result_id)** function.

To rerun all analysis with errors, you can use **redo_error_analysis** function.

To delete all simulations and results that have errors, you can use **delete_all_errors** function.

To delete all data in all tables, you can use **delete_all_data** function.

To transfer data in a database between different clusters, 
you can take the database from the other cluster and use **transfer_database(path_to_database, run_names)**,
where _path_to_database_ is the path to the database copied from the other cluster 
and run_names is a list of _run_names_ of which data you want to transfer.

### 4.3 Working of the code
When **run_several_simulations.py** is called, it puts the new simulations into the database and calls **check_queue**.

**Check_queue.py** then checks the queue, 
and if there are some free GPU/CPU units based on the maximum number in the settings file, 
it sends the simulation to the queue.

Based on the simulation type, it then calls ti1p1/ti1p2/ti2p1/ti2p2, 
which creates necessary input files and sends the job to the queue.

When the job starts running, ends, or error happens, **update_job_status** is called. 
It updates job_status in the database, and if the job has ended, 
it can send some more simulations to the database and call **check_queue**.

When the ti2p2 has ended, it calls **analyse_data_after_run**, which analyses all the data and puts them into the database.

## 5 Known issues
Sometimes you can get "_database closed_" error - that can happen when several codes access the database at the same time.
In that case, you might need to run the simulation or analysis again - depending on when the error happened.

During analysis, you can get UNIQUE constraint error, 
when analysis of the same simulation has already been initiated once in the database.
If you would like to run the analysis again, 
you need to run a **redo_analysis(result_id)** function in **database_helper.py**.

In some proteins, there might be an error with equilibration between different lambda states, and it will show in slurm 
PMEMD Terminated abruptly and in the relevant .out file, you will find that the mask atoms don't match.
In that case, you need to equilibrate manually from a different lambda state.
You should not only re-equilibrate the lambda state where the error happened, 
but also first the state before in the order.
For example, if the error happened in lambda state 8, you should first re-equilibrate 7 from lambda state 5 
and then 8 from lambda state 5 as well to prevent any further errors.

## 6 Examples of input files

### 6.1 Settings file

```text
GPU_setting="#SBATCH –partition=compchemq 
#SBATCH –qos=compchem 
#SBATCH –account=compchem_acc 
#SBATCH –mem=40g 
#SBATCH -N1 –ntasks-per-node=1 
#SBATCH–cpus-per-task=1 
#SBATCH –ntasks-per-socket=1 
#SBATCH –gres=gpu:1 
#SBATCH –exclude=compchemq1
module purge 
module load amber-uon/cuda11/20bectgtx-eb-GCCcore-10.2.0"
CPU_setting="#SBATCH –partition=shortq 
#SBATCH –mem=40g 
#SBATCH -N1 –ntasks-per-node=1 
#SBATCH –cpus-per-task=40 
#SBATCH –ntasks-per-socket=1
module purge 
module load amber-uon/intelmpi2019/20volta"
environment="module load anaconda-uon/3 
source activate alchem"
home_pathway="C:/Users/knirs/PycharmProjects/AmberTI/pytest" 
max_GPUs="15"
max_CPUs="14"
```

### 6.2 Example of modification file

If you want to modify some of the simulation parameters only for certain runs,
you can use a modification file.
The modification file has the following structure:
- First you need a line with a type of simulation to change (ti1p1/ti1p2/ti2p1/ti2p2)
- Then if you modify ti1 simulations, you need to put on another line the seperate simulation (e.g. 01_min, 02_min, …)
- Then you can put the simulations to change/add in a format **parameter=value** e.g. ntpr=1000
- If you want to delete certain parameter, you need to put **parameter=DELETE** (e.g. ntpr=DELETE)
- At the end of each section, you need to put line **&end**

At the moment, it is unfortunately not possible to modify anything that is usually written after the **&end** line.
Example of such file would be:
```text
ti1p1
01_min
iwrap=2
cut=10.0
maxcyc=100
&end
02_min
maxcyc=100
iwrap=2
&end
ti2p1
maxcyc=100
ntwx=DELETE
&end
```
## References
Weighted_cc was adopted from following article:
Li, Yishui & Liu, Runduo & Liu, Jie & Luo, Haibin & Wu, Chengkun & Li, Zhe. An Open Source Graph-Based Weighted Cycle Closure Method for Relative Binding Free Energy Calculations. Journal of Chemical Information and Modeling. 2023, 63, 2, 561–570

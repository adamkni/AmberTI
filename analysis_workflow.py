""" Calculates all free energy differences for a given complex using the ABFE workflow.

    This script collects data from molecular dynamics simulations and estimates free energy differences using the
    ABFE workflow.

    Command-line Arguments:
        -s, --skiptime: Discard data prior to this specified time as 'equilibration' data. Unit picoseconds.
                        Default: 0 ps.
        -c, --complex: The complex name. (required)
        -p, --prefix: Prefix after the complex name. (required)
    """

import argparse
import os
import pathlib
import pickle
import sys

from alchemlyb.workflows import ABFE

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect data and estimate free energy differences",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter, )
    parser.add_argument("-s", "--skiptime",
                        help="Discard data prior to this specified time as 'equilibration' data. Units picoseconds. "
                             "Default: 0 ps.",
                        default=0, type=float, )
    parser.add_argument("-c", "--complex", help="The complex name.", required=True, )
    parser.add_argument("-p", "--prefix", help="Prefix after the complex name.", required=True, )

    args = parser.parse_args(sys.argv[1:])
    pre = args.complex + args.prefix
    skip_time = args.skiptime

    workflow = ABFE(software='AMBER', dir='./', prefix=f'*/{pre}', suffix='out', T=300, outdirectory='./')

    # Set the unit to kcal/mol
    workflow.update_units('kcal/mol')

    # Read the data
    workflow.read(read_u_nk=False)

    # Decorrelate the data
    workflow.preprocess(skiptime=skip_time, uncorr='dhdl', threshold=50)

    # Run the estimator
    workflow.estimate(estimators=['TI'])

    # Retrieve the result
    summary = workflow.generate_result()

    # Save the summary to a pickle file
    pickle.dump(summary, open("result.p", "wb"))

    # Print the summary
    print(summary)

    # Save the summary as a CSV file
    summary.round(6).to_csv("results.csv")

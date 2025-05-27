#!/bin/python3

"""Helper functions for reading and modifying settings from the
settings file."""
import re
import os
import sys


# settings_path = os.path.join('~', '.ti_sim.config')
settings_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.ti_sim.config')

def set_settings_path(path):
    """Save the settings file path.

    Saves the given path to the .ti_sim.config file.

    Parameters
    ----------
    path : str
        Path to settings file.

    """
    # Checks if the file exists and if not throws an error
    if not os.path.isfile(path):
        print(f"ERROR: {path} does not exist. You need to create the settings file first.")
        exit(1)
    # Check if there is everything that should be in the settings file
    with open(settings_path, 'w') as file:
        file.write(path)
    with open(path, 'r') as file:
        data = file.read()

        # Check if the settings file has all the data it should have
        if 'home_pathway=' not in data or 'GPU_setting=' not in data or 'CPU_setting=' not in data or 'environment=' not in data or 'max_CPUs=' not in data or 'max_GPUs=' not in data:
            print("ERROR: The settings file is not in the correct format. Please check the README for more information.")
            exit(1)

    print("Settings path set to: %s" % path)


def get_settings_path():
    """Get the saved path to the settings file."""
    with open(settings_path, 'r') as file:
        path = file.read()
    return path


def get_settings_data():
    """Get the data from the settings file."""
    with open(get_settings_path(), 'r') as file:
        data = file.read()
    return data


def find_between(s, start, end):
    """Find a substring between two substrings."""
    return re.search('%s(.*?)%s' % (start, end), s, re.DOTALL).group(1)


def get_home_pathway():
    """Get the home pathway."""
    home_pathway = find_between(get_settings_data(), 'home_pathway="', '"')
    return home_pathway


def get_gpu_settings():
    """Get the GPU settings."""
    settings_data = get_settings_data()
    gpu_settings = find_between(settings_data, 'GPU_setting="', '"')
    return gpu_settings


def get_cpu_settings():
    """Get the CPU settings."""
    settings_data = get_settings_data()
    cpu_settings = find_between(settings_data, 'CPU_setting="', '"')
    return cpu_settings


def get_environment():
    """Get the environment."""
    settings_data = get_settings_data()
    environment = find_between(settings_data, 'environment="', '"')
    return environment


def get_max_cpus():
    """Get the maximum number of CPUs to be used at once."""
    return int(find_between(get_settings_data(), 'max_CPUs="', '"'))


def get_max_gpus():
    """Get the maximum number of GPUs to be used at once."""
    return int(find_between(get_settings_data(), 'max_GPUs="', '"'))

def get_amberti_path():
    """Get the path to the amberti folder."""
    return os.path.dirname(os.path.realpath(__file__))


if __name__ == '__main__':
    globals()[sys.argv[1]](sys.argv[2])

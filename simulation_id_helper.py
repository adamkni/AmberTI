"""Helper functions for parsing simulation IDs."""

import re


def get_complex_name(simulation_id):
    """Get complex name from simulation ID string.

    Parameters
    ----------
    simulation_id : str
        The simulation ID string.

    Returns
    -------
    str
        Complex name parsed from simulation ID.

    """
    return simulation_id.split('_')[0].strip()


def get_run_name(simulation_id):
    """Get run name from simulation ID string.

    Parameters
    ----------
    simulation_id : str
        The simulation ID string.

    Returns
    -------
    str
        Run name parsed from the simulation ID.

    Raises
    ------
    ValueError
        If run name cannot be parsed.

    """
    matches = re.findall(r'(?:[^_]*_){3}(.*)', simulation_id)
    if matches:
        return matches[0]
    else:
        raise ValueError("There is invalid line in the queue file.")


def get_run_name_from_result_id(result_id):
    """Get run name from result ID string.

    Parameters
    ----------
    result_id : str
        The result ID string.

    Returns
    -------
    str
        Run name parsed from the result ID.

    Raises
    ------
    ValueError
        If run name cannot be parsed.

    """
    matches = re.findall(r'(?:[^_]*_){1}(.*)', result_id)
    if matches:
        return matches[0]
    else:
        raise ValueError("The result ID is invalid.")


def get_ligand_one(simulation_id):
    """Get the first ligand name from simulation ID.

    Parameters
    ----------
    simulation_id : str
        The simulation ID string.

    Returns
    -------
    str
        First ligand name parsed from simulation ID.

    """
    return get_complex_name(simulation_id).split('-')[0].strip()


def get_ligand_two(simulation_id):
    """Get the second ligand name from simulation ID.

    Parameters
    ----------
    simulation_id : str
        The simulation ID string.

    Returns
    -------
    str
        Second ligand name parsed from ID.

    """
    return get_complex_name(simulation_id).split('-')[1].strip()


def get_is_wat(simulation_id):
    """Check if simulation ID is for water leg.

    Parameters
    ----------
    simulation_id : str
        The simulation ID string.

    Returns
    -------
    bool
        True if water leg, False otherwise.

    """
    return 'wat' in simulation_id


def get_mode(simulation_id):
    """Get the simulation mode from the ID string.

    Parses the mode number and maps it to the mode name.

    Parameters
    ----------
    simulation_id : str
        The simulation ID string.

    Returns
    -------
    str
        The simulation mode name.

    Raises
    ------
    ValueError
        If invalid mode number.

    """
    mode_number = simulation_id.split('_')[1].strip()
    if mode_number == '1':
        return 'ti1p1'
    elif mode_number == '2':
        return 'ti1p2'
    elif mode_number == '3':
        return 'ti2p1'
    elif mode_number == '4':
        return 'ti2p2'
    else:
        raise ValueError("There is invalid line in the queue file.")


def get_result_id(simulation_id):
    """Get result ID for a simulation ID string.

    Parameters
    ----------
    simulation_id : str
        The simulation ID string.

    Returns
    -------
    str
        Result ID in form <complex>_<run_name>

    """
    return get_complex_name(simulation_id) + '_' + get_run_name(simulation_id)


def get_strictly_complex_name(simulation_id):
    """Get complex name without -wat if present.

    Parameters
    ----------
    simulation_id : str
        The simulation ID string.

    Returns
    -------
    str
        Complex name with -wat removed if present.

    """
    if 'wat' not in get_complex_name(simulation_id):
        return get_complex_name(simulation_id)
    else:
        return get_complex_name(simulation_id).split('-wat')[0].strip()


def get_updated_simulation_id(simulation_id):
    """Update simulation ID mode number.

        Increments the mode number in the ID by 1.

        Parameters
        ----------
        simulation_id : str
            The simulation ID string.

        Returns
        -------
        str
            Updated simulation ID with incremented mode.

        """
    parts = simulation_id.split('_')
    parts[1] = str(int(parts[1]) + 1)
    return '_'.join(parts)

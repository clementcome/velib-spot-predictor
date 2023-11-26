"""Utility functions for the velib_spot_predictor package."""
from pathlib import Path


def get_one_filepath(folder: Path, pattern: str) -> Path:
    """Get the filepath of the first file matching the pattern in the folder.

    Parameters
    ----------
    folder : Path
        Folder where to look for the file
    pattern : str
        Pattern to match the file


    Returns
    -------
    Path
        Path to the matched file


    Raises
    ------
    ValueError
        If no file or more than one file is found matching the pattern in the
        folder
    """
    filepath_list = list(folder.glob(pattern))
    if len(filepath_list) != 1:
        raise ValueError(
            f"Found {len(filepath_list)} files matching the pattern {pattern}"
            f" in folder {folder}"
        )
    return filepath_list[0]

"""
This module provides functions to retrieve and update album-level metadata from a list of FLAC
files.
"""

from collections import Counter, defaultdict
import os

from mutagen.flac import FLAC

# The following metadata keys are used to retrieve album metadata from track files.
# TRACK_META_KEYS = ['artist', 'title', 'work', 'part', 'composer']
ALBUM_META_KEYS = ["album", "albumartist", "genre", "discnumber", "disctotal"]


def read_folder(folder_path):
    """
    Reads a folder and returns a list of paths to all FLAC files in the folder.

    Args:
        folder_path (str): The path to the folder to be read.

    Returns:
        list: A list of sorted paths to all FLAC files in the folder.
    """
    flac_files = []
    for _, _, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(".flac"):
                flac_files.append(filename)
    flac_files.sort()
    return [os.path.join(folder_path, f) for f in flac_files]


def top_element(lst):
    """
    Returns the most frequently occurring element in a list.

    Args:
        lst (list): The input list.

    Returns:
        str: The most frequently occurring element in the list. Return None if lst is empty.
    """
    if not lst:
        return None
    counts = Counter(lst)
    result, _ = counts.most_common(1)[0]
    return result


def hashable(val):
    """
    Converts an input value to a hashable one if needed.

    The input value can be either string, tuple of strings, and list of strings.
    Only the list of strings will be converted to tuple of strings.
    If the tuple constains only one string, it will be converted to a string.
    If the tuple is empty, it will return an empty string.

    Args:
        obj (string, tuple of strings, list of strings)

    Returns:
        A hashable object, either a string or a tuple of strings.

    Examples:
        >>> hashable(['a1', 'b2', 'c3'])
        ('a1', 'b2', 'c3')
        >>> hashable(('a1', 'b2', 'c3'))
        ('a1', 'b2', 'c3')
        >>> hashable('str')
        'str'
        >>> hashable(['alone'])
        'alone'
    """
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        val = tuple(val)
    if len(val) == 1:
        return val[0]
    return val


def retrieve_album_metadata(track_files):
    """
    Retrieves album-level metadata from a list of FLAC files.

    The album level metadata should be the same for all FLAC files in the list.
    If not, the top value is selected.

    Args:
        flac_files (list): A list of file paths to FLAC files, assuming they are all from the same 
        album.

    Returns:
        dict: A dictionary containing the album-level metadata. The dictionary has the following 
        structure:
            {
                'album_meta_key1': (suggested_value1, {i-th track: diff_value, ...}),
                'album_meta_key2': (suggested_value2, {i-th track: diff_value, ...}),
                ...
            }
    """
    album_metadata_all_tracks = defaultdict(list)
    for track_file in track_files:
        track = FLAC(track_file)
        for key in ALBUM_META_KEYS:
            value = hashable(track.get(key, ""))
            if value:
                album_metadata_all_tracks[key].append(value)
    top_value = {}
    diff_values = {}
    for key in ALBUM_META_KEYS:
        top_value[key] = top_element(album_metadata_all_tracks[key])
        diff_values[key] = dict()

    for track, track_file in enumerate(track_files, 1):
        track = FLAC(track_file)
        for key in ALBUM_META_KEYS:
            value = hashable(track.get(key, ""))
            if value != top_value[key]:
                diff_values[key][track] = value
    result = {}
    for key in ALBUM_META_KEYS:
        result[key] = (top_value[key], diff_values[key])
    return result


def update_track_work(track_files, track_work_part, dry_run=True, verbose=True):
    """
    Updates the input track's metadata based on the given track to work, part mapping.

    A work means a classical music piece/composition, and a part means a movement within a work.
    Use 'work' and 'part' metadata fields to store the work and part information to comply with the
    Roon's guideline: "File Tag Best Practice" 
    (https://help.roonlabs.com/portal/en/kb/articles/file-tag-best-practice)
    Also, a track's title will be updated to f"{work} - {part}".

    Args:
        track_files (list): A list of file paths to the FLAC files, assuming track number starts
          from 1.
        track_work_part (dict): A dictionary mapping of a track number to a tuple of work and
          part. Note that only tracks mentioned here will be updated.
        dry_run (bool, optional): If True, only print the original and proposed metadata without
                                  saving the changes.
                                  If False, update and save the metadata. Default is True.
        verbose (bool, optional): If True, print the original and proposed metadata. Default True.

    Returns:
        None
    """

    def print_track_metadata(track):
        print(f"\tTitle: {track.get('title', '')}")
        print(f"\tWork: {track.get('work', '')}")
        print(f"\tPart: {track.get('part', '')}")

    for track_number, track_filename in enumerate(track_files, 1):
        track = FLAC(track_filename)
        if verbose:
            print(f"track: {track_number}")
            print_track_metadata(track)
        if track_number in track_work_part:
            work, part = track_work_part[track_number]
            track["title"] = f"{work} - {part}"
            track["work"] = work
            track["part"] = part
        if not dry_run:
            track.save()
        if verbose:
            print("proposed:" if dry_run else "updated metadata:")
            print_track_metadata(track)


def propose_track_rename(track_files, verbose=True):
    """
    Proposes new filenames for a list of track files based on their title in metadata.

    Args:
        track_files (list): A list of file paths to the track files.
        verbose (bool, optional): If True, print the original and proposed filenames.

    Returns:
        list: A list of tuples containing the original file path and the proposed new file path
          for each track file.
    """
    result = []
    album_dir_name = None
    for track_path in track_files:
        track = FLAC(track_path)
        basename = os.path.basename(track_path)
        dirname = os.path.dirname(track_path)
        extname = os.path.splitext(basename)[1]
        reserved_part = basename.split("-")[0].strip()
        new_filename = f"{reserved_part} - {track['title'][0]}.{extname}"
        new_file_path = os.path.join(dirname, new_filename)
        result.append((track_path, new_file_path))
        if verbose:
            if not album_dir_name:
                # Assume all tracks are in the same album directory.
                album_dir_name = dirname
                print(f"Album directory: {album_dir_name}")
            if new_file_path != track_path:
                print(f"\t{basename} -> {new_filename}")
    return result


def exec_file_rename(proposal):
    """
    Renames files based on the given name change proposal.

    Args:
        proposal (list): A list of tuples containing the old and new paths of the files to be
          renamed.

    Returns:
        None
    """
    for old_path, new_path in proposal:
        os.rename(old_path, new_path)

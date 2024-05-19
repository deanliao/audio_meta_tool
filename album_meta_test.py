import pytest

import os
import mutagen
import shutil
import tempfile

from album_meta import hashable
from album_meta import read_folder
from album_meta import retrieve_album_metadata
from album_meta import top_element

TEST_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "testdata")
FLAC_SAMPLE = os.path.join(TEST_DIR, "silent_quarter-second.flac")

def test_read_folder():
    # Create a temporary folder and some FLAC files for testing
    with tempfile.TemporaryDirectory() as folder_path:
        file_names = ['file1.flac', 'file2.flac', 'file3.txt', 'file4.flac']
        for file_name in file_names:
            file_path = os.path.join(folder_path, file_name)
            open(file_path, 'w').close()

        # Call the read_folder function
        result = read_folder(folder_path)

        # Assert that the result is a list of sorted paths to FLAC files
        expected_result = [
            os.path.join(folder_path, 'file1.flac'),
            os.path.join(folder_path, 'file2.flac'),
            os.path.join(folder_path, 'file4.flac')
        ]
        assert result == expected_result

def test_hashable():
    assert hashable(['a1', 'b2', 'c3']) == ('a1', 'b2', 'c3')
    assert hashable(('t1', 't2', 't3')) == ('t1', 't2', 't3')
    assert hashable(['alone']) == 'alone'
    assert hashable(('single_t', )) == 'single_t'
    assert hashable('str') == 'str'

def test_top_element():
    # Test case 1: Empty list
    lst = []
    assert top_element(lst) is None

    # Test case 2: List with a single element
    lst = [5]
    assert top_element(lst) == 5

    # Test case 3: List with multiple elements, one element occurs most frequently
    lst = [1, 2, 3, 2, 2, 4, 5, 2]
    assert top_element(lst) == 2

    # Test case 4: List with multiple elements, multiple elements occur with the same frequency
    lst = [1, 2, 3, 4, 5]
    assert top_element(lst) == 1  # Since all elements occur once, the first element is returned

    # Test case 5: List with multiple elements, some elements occur with the same top frequency
    lst = [1, 2, 2, 3, 3]
    assert top_element(lst) == 2  # The first top element is returned

def __create_flac_files_with_metadata(file_names, metas):
    for path, meta in zip(file_names, metas):
        shutil.copy(FLAC_SAMPLE, path)
        f = mutagen.flac.FLAC(path)
        for key, value in meta.items():
            f[key] = value
        f.save()

def test_retrieve_album_metadata():
    # Create a temporary folder and some FLAC files for testing
    track_names = ['track_01.flac', 'track_02.flac', 'track_03.flac']
    track_metas = [
        {'album': 'Album 1', 'albumartist': 'Alice', 'genre': 'Genre 1', 'discnumber': '1', 'disctotal': '2'},
        {'album': 'Album 1', 'albumartist': 'Bob', 'discnumber': '1', 'disctotal': '2'},
        {'albumartist': 'Alice', 'discnumber': '1', 'disctotal': '2'},
    ]
    with tempfile.TemporaryDirectory() as folder_path:
        track_paths = [os.path.join(folder_path, file_name) for file_name in track_names]
        __create_flac_files_with_metadata(track_paths, track_metas)
        
        # Call the function with mock FLAC objects
        result = retrieve_album_metadata(track_paths)

        # Assert the expected result
        expected_result = {
            'album': ('Album 1', {3: ''}),
            'albumartist': ('Alice', {2: 'Bob'}),
            'genre': ('Genre 1', {2: '', 3: ''}),
            'discnumber': ('1', {}),
            'disctotal': ('2', {})
        }
        assert result == expected_result

def test_retrieve_album_metadata_multi_artist():
    # Create a temporary folder and some FLAC files for testing
    track_names = ['track_01.flac', 'track_02.flac', 'track_03.flac']
    track_metas = [
        {'album': 'Album 1', 'albumartist': ['Alice', 'Bob'], 'genre': 'Genre 1', 'discnumber': '1', 'disctotal': '2'},
        {'album': 'Album 1', 'albumartist': ['Bob'], 'discnumber': '1', 'disctotal': '2'},
        {'albumartist': ['Alice', 'Bob'], 'discnumber': '1', 'disctotal': '2'},
    ]
    with tempfile.TemporaryDirectory() as folder_path:
        track_paths = [os.path.join(folder_path, file_name) for file_name in track_names]
        __create_flac_files_with_metadata(track_paths, track_metas)
        
        # Call the function with mock FLAC objects
        result = retrieve_album_metadata(track_paths)

        # Assert the expected result
        expected_result = {
            'album': ('Album 1', {3: ''}),
            'albumartist': (('Alice', 'Bob'), {2: 'Bob'}),
            'genre': ('Genre 1', {2: '', 3: ''}),
            'discnumber': ('1', {}),
            'disctotal': ('2', {})
        }
        assert result == expected_result


test_read_folder()
test_hashable()
test_top_element()
test_retrieve_album_metadata()

#!/usr/bin/env python
"""
`htrc.mock.volumes`

Contains functions to test the volume retrieval from the HTRC Data API.
The download functions will return a sample zip file.

See the core documentation for an example of how to use this library.
"""
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

from builtins import input

from configparser import RawConfigParser as ConfigParser
from io import BytesIO
import os, os.path
from zipfile import ZipFile  # used to decompress requested zip archives.

from htrc.lib.cli import bool_prompt
from htrc.config import save_credentials
from htrc.auth import credential_prompt

EXAMPLE_FILE = os.path.join(os.path.dirname(__file__), 'example.zip')

def get_volumes(token, volume_ids, concat=False):
    """
    Returns volumes from the Data API as a raw zip stream.

    Parameters:
    :token: An OAuth2 token for the app.
    :volume_ids: A list of volume_ids
    :concat: If True, return a single file per volume. If False, return a single
    file per page (default).
    """
    if not volume_ids:
        raise ValueError("volume_ids is empty.")

    with open(EXAMPLE_FILE, 'rb') as infile:
        data = infile.read()

    return data

def get_pages(token, page_ids, concat=False):
    """
    Returns a ZIP file containing specfic pages.
    
    Parameters:
    :token: An OAuth2 token for the app.
    :volume_ids: A list of volume_ids
    :concat: If True, return a single file per volume. If False, return a single
    file per page (default).
    """
    if not page_ids:
        raise ValueError("page_ids is empty.")
    
    with open(EXAMPLE_FILE, 'rb') as infile:
        data = infile.read()

    return data

def get_oauth2_token(username, password):
    """
    Returns a sample token for oauth2
    """
    return 'a1b2c3d4e5f6'


def credentials_from_config(path):
    """
    Retrieves the username and password from a config file for the Data API.
    DOES NOT raise an EnvironmentError if path is invalid.
    See also: credential_prompt
    """
    username = None
    password = None

    return (username, password)


def download_volumes(volume_ids, output_dir, username=None, password=None):
    # create output_dir folder, if nonexistant
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Retrieve token and download volumes
    token = get_oauth2_token(username, password)
    data = get_volumes(token, volume_ids, False)

    with open(EXAMPLE_FILE, 'rb') as infile:
        myzip = ZipFile(infile)
        myzip.extractall(output_dir)
        myzip.close()


def download(args):
    # extract files
    with open(args.file) as IDfile:
        volumeIDs = [line.strip() for line in IDfile]

    return download_volumes(volumeIDs, args.output, args.username, args.password)


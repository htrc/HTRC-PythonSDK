#!/usr/bin/env python
"""
`htrc.volumes`

Contains functions to retrieve volumes from the HTRC Data API. 

The functions in this package will not operate unless they are 
executed from an HTRC Data Capsule in Secure Mode. The module 
`htrc.mock.volumes` contains Patch objects for testing workflows.
"""
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

from builtins import input

import http.client
from io import BytesIO  # used to stream http response into zipfile.
import json
import logging
import os.path
import progressbar
import re
import socket
import ssl
import sys
from time import sleep
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import quote_plus, urlencode
import xml.etree.ElementTree as ET
from zipfile import ZipFile  # used to decompress requested zip archives.

from htrc.lib.cli import bool_prompt
import htrc.config

import logging
from logging import NullHandler
logging.getLogger(__name__).addHandler(NullHandler())

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

    url = htrc.config.get_dataapi_epr() + "volumes"
    data = {'volumeIDs': '|'.join(
        [id.replace('+', ':').replace('=', '/') for id in volume_ids])}
    if concat:
        data['concat'] = 'true'

    # Authorization
    headers = {"Authorization": "Bearer " + token,
               "Content-type": "application/x-www-form-urlencoded"}

    # Create SSL lookup
    # TODO: Fix SSL cert verification
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Retrieve the volumes
    host, port = htrc.config.get_host_port()
    httpsConnection = http.client.HTTPSConnection(host, port, context=ctx)
    httpsConnection.request("POST", url, urlencode(data), headers)

    response = httpsConnection.getresponse()

    if response.status is 200:
        body = True
        data = BytesIO()
        bytes_downloaded = 0
        bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength,
            widgets=[progressbar.AnimatedMarker(), '    ',
                     progressbar.DataSize(),
                     ' (', progressbar.FileTransferSpeed(), ')'])

        while body:
            body = response.read(128)
            data.write(body)
            bytes_downloaded += len(body)
            bar.update(bytes_downloaded)

        data = data.getvalue()
    else:
        logging.warning("Unable to get volumes")
        logging.warning("Response Code: {}".format(response.status))
        logging.warning("Response: {}".format(response.reason))
        raise EnvironmentError("Unable to get volumes.")

    if httpsConnection is not None:
        httpsConnection.close()

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

    url = htrc.config.get_dataapi_epr()
    url += "pages?pageIDs=" + quote_plus('|'.join(page_ids))
    if concat:
        url += "&concat=true"

    logging.info("data api URL: ", url)
    
    # Create SSL lookup
    # TODO: Fix SSL cert verification
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Create connection
    host, port = htrc.config.get_host_port()
    httpsConnection = http.client.HTTPSConnection(host, port, context=ctx)

    headers = {"Authorization": "Bearer " + token}
    httpsConnection.request("GET", url, headers=headers)

    response = httpsConnection.getresponse()

    if response.status is 200:
        data = response.read()
    else:
        logging.warning("Unable to get pages")
        logging.warning("Response Code: ".format(response.status))
        logging.warning("Response: ".format(response.reason))
        raise EnvironmentError("Unable to get pages.")

    if httpsConnection is not None:
        httpsConnection.close()

    return data

def get_jwt_token():
    # Currently we just store one common jwt token locally at .htrc file for simplicity
    # Expect to add POST method to query unique jwt token with the combo of username and password
    return htrc.config.get_jwt_token()


def get_oauth2_token(username, password):
    # make sure to set the request content-type as application/x-www-form-urlencoded
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    data = { "grant_type": "client_credentials",
             "client_secret": password,
             "client_id": username }
    data = urlencode(data)

    # create an SSL context
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # make sure the request method is POST
    host, port = htrc.config.get_oauth2_host_port()
    oauth2port = htrc.config.get_oauth2_port()
    oauth2EPRurl = htrc.config.get_oauth2_url()
    httpsConnection = http.client.HTTPSConnection(host, oauth2port, context=ctx)
    httpsConnection.request("POST", oauth2EPRurl + "?" + data, "", headers)

    response = httpsConnection.getresponse()

    # if response status is OK
    if response.status == 200:
        data = response.read().decode('utf8')

        jsonData = json.loads(data)
        logging.info("*** JSON: {}".format(jsonData))

        token = jsonData["access_token"]
        logging.info("*** parsed token: {}".format(token))

    else:
        logging.warning("Unable to get token")
        logging.warning("Response Code: {}".format(response.status))
        logging.warning("Response: {}".format(response.reason))
        logging.warning(response.read())
        raise EnvironmentError("Unable to get token.")

    if httpsConnection is not None:
        httpsConnection.close()

    return token


def download_volumes(volume_ids, output_dir, username=None, password=None,
                     config_path=None):
    # create output_dir folder, if nonexistant
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # get credentials if not specified
    if not username and not password:
        username, password = htrc.config.get_credentials(config_path)
    
    # Retrieve token and download volumes
    # token = get_oauth2_token(username, password)
    token = get_jwt_token()
    if token is not None:
        logging.info("obtained token: %s\n" % token)

        try:
            data = get_volumes(token, volume_ids, False)

            myzip = ZipFile(BytesIO(data))
            myzip.extractall(output_dir)
            myzip.close()
        except socket.error:
            raise RuntimeError("Data API request timeout. Is your Data Capsule in Secure Mode?")

    else:
        raise RuntimeError("Failed to obtain oauth token.")


def download(args):
    # extract files
    with open(args.file) as IDfile:
        volumeIDs = [line.strip() for line in IDfile]

    return download_volumes(volumeIDs, args.output, args.username, args.password)

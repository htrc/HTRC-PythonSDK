from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

import sys
if sys.version_info.major == 2:
    from mock import Mock, patch, PropertyMock
elif sys.version_info.major == 3:
    from unittest.mock import Mock, patch, PropertyMock

from io import BytesIO  # used to stream http response into zipfile.
from tempfile import NamedTemporaryFile, mkdtemp
import unittest2 as unittest

import htrc.auth
import htrc.config
import htrc.volumes

class MockResponse(BytesIO):
    def __init__(self, data, status=200, *args, **kwargs):
        BytesIO.__init__(self, data, *args, **kwargs)
        self.status = status

class TestVolumes(unittest.TestCase):
    def setUp(self):
        self.test_vols = ['mdp.39015050817181', 'mdp.39015055436151',
            'mdp.39015056169157', 'mdp.39015050161697', 'mdp.39015042791874']

        self.config_path = NamedTemporaryFile(delete=False).name
        self.empty_config_path = NamedTemporaryFile(delete=False).name

        self.output_path = mkdtemp()

    def tearDown(self):
        import os, shutil
        os.remove(self.config_path)
        shutil.rmtree(self.output_path)


    @patch('htrc.volumes.http.client.HTTPSConnection')
    def test_get_volumes_and_pages(self, https_mock):
        response_mock = Mock(status=200)
        response_mock.read.return_value =\
            ''.encode('utf8')
        https_mock.return_value.getresponse.return_value = response_mock

        htrc.volumes.get_volumes('1234', self.test_vols)
        htrc.volumes.get_pages('1234', self.test_vols)

    @patch('htrc.volumes.http.client.HTTPSConnection')
    def test_get_volumes_and_pages_error(self, https_mock):
        response_mock = Mock(status=500)
        https_mock.return_value.getresponse.return_value = response_mock

        with self.assertRaises(EnvironmentError):
            htrc.volumes.get_volumes('1234', self.test_vols)

        with self.assertRaises(EnvironmentError):
            htrc.volumes.get_pages('1234', self.test_vols)

    def test_get_volumes_and_pages_empty(self):
        with self.assertRaises(ValueError):
            htrc.volumes.get_volumes('1234', [])

        with self.assertRaises(ValueError):
            htrc.volumes.get_pages('1234', [])

    @patch('htrc.volumes.ZipFile')
    @patch('htrc.volumes.get_volumes')
    @patch('htrc.auth.get_jwt_token')
    @patch('htrc.volumes.http.client.HTTPSConnection')
    def test_download_volumes(self, https_mock, jwt_mock, volumes_mock,
                              zip_mock):
        response_mock = Mock(status=200)
        https_mock.return_value.getresponse.return_value = response_mock
        jwt_mock.return_value = 'a1b2c3d4e5'
        volumes_mock.return_value = b''

        htrc.volumes.download_volumes(self.test_vols, self.output_path,
            username='1234', password='1234')

        # test directory creation
        import shutil
        shutil.rmtree(self.output_path)
        htrc.volumes.download_volumes(self.test_vols, self.output_path,
            username='1234', password='1234')

    # TODO: Fix this test for case where config file exists, but creds not set
    """
    @patch('htrc.volumes.ZipFile')
    @patch('htrc.volumes.get_volumes')
    @patch('htrc.volumes.get_oauth2_token')
    @patch('htrc.volumes.http.client.HTTPSConnection')
    def test_download_volumes_saved_creds(self, https_mock, oauth2_mock, volumes_mock,
                              zip_mock):
        response_mock = Mock(status=200)
        https_mock.return_value.getresponse.return_value = response_mock
        oauth2_mock.return_value = 'a1b2c3d4e5'
        volumes_mock.return_value = b''

        # test config-based auth
        import os, os.path
        config_path = os.path.expanduser('~')
        config_path = os.path.join(config_path, '.htrc')
        preexisting_config = os.path.exists(config_path)
        if not preexisting_config:
            htrc.config.save_credentials('1234', '1234', config_path)

        htrc.volumes.download_volumes(self.test_vols, self.output_path)

        if not preexisting_config:
            os.remove(config_path)
    """

    def test_download(self):
        pass

suite = unittest.TestLoader().loadTestsFromTestCase(TestVolumes)
unittest.TextTestRunner(verbosity=2).run(suite)


import os
import unittest

from mock import Mock

from domain.operations.autoload import AutolaodOperation
from domain.services.clients import ApiClientsProvider


class IntegrationTestAutolaodOperation(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_validate_config_with_user_and_pass(self):
        # arrange
        cloud_provider_resource = Mock(config_file_path='c:\\temp\\docker-for-desktop-config.txt')

        autoload_operation = AutolaodOperation(ApiClientsProvider())
        autoload_operation.validate_config(cloud_provider_resource)

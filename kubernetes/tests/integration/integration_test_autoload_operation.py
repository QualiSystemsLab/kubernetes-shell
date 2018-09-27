import unittest

from mock import Mock

from domain.operations.autoload import AutolaodOperation
from domain.services.clients import ApiClientsProvider


class IntegrationTestAutolaodOperation(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_validate_config(self):
        # arrange
        cloud_provider_resource = Mock(cluster_name='docker-for-desktop-cluster')

        autoload_operation = AutolaodOperation(ApiClientsProvider())
        autoload_operation.validate_config(cloud_provider_resource)

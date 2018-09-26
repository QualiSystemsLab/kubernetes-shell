import unittest

from mock import Mock

from domain.operations.cleanup import CleanupSandboxInfraOperation
from domain.services.clients import ApiClientsProvider
from domain.services.namespace import KubernetesNamespaceService


class IntegrationTestCleanupSandboxInfraOperation(unittest.TestCase):

    def test_cleanup(self):
        # arrange
        sandbox_id = 'af213574-3f61-496e-a9a1-25d647ff8b18'

        cloud_provider_resource = Mock(cluster_name='docker-for-desktop-cluster')
        clients = ApiClientsProvider().get_api_clients(cloud_provider_resource.cluster_name)

        namespace_service = KubernetesNamespaceService()

        action = Mock(actionId='xxxx')
        
        # act
        CleanupSandboxInfraOperation(namespace_service).cleanup(Mock(), clients, sandbox_id, action)

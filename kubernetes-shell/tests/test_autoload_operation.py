import unittest

from mock import Mock

from domain.operations.autoload import AutolaodOperation
from domain.operations.delete import DeleteInstanceOperation
from domain.services.clients import ApiClientsProvider
from domain.services.deployment import KubernetesDeploymentService


class TestAutoloadOperation(unittest.TestCase):
    def setUp(self):
        self.api_clients_provider = ApiClientsProvider()
        self.deployment_service = KubernetesDeploymentService()
        self.autoload_operation = AutolaodOperation(self.api_clients_provider, self.deployment_service)

    def tearDown(self):
        pass

    def test_get_deployed_app_autoload_data(self):
        # arrange
        deployed_app = Mock()
        clients = Mock()

        pod1 = Mock()
        pod2 = Mock()
        pod3 = Mock()
        self.deployment_service.get_pods_by_name = Mock(return_value=[pod1, pod2, pod3])

        # act
        result = self.autoload_operation.get_deployed_app_autoload_data(clients=clients,
                                                                        deployed_app=deployed_app)

        # assert
        self.assertItemsEqual([{'PodIP': pod1.status.pod_ip}, {'PodIP': pod2.status.pod_ip}, {'PodIP': pod3.status.pod_ip}], result)

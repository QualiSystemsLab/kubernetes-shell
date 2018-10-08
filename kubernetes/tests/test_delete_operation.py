import unittest

from mock import Mock

from domain.operations.delete import DeleteInstanceOperation


class TestDeleteOperation(unittest.TestCase):

    def test_delete_basic_flow(self):
        # arrange
        logger = Mock()
        clients = Mock()
        kubernetes_app_name = Mock()
        deployed_app_name = Mock()
        namespace = Mock()

        networking_service = Mock()
        deployment_service = Mock()
        delete_operation = DeleteInstanceOperation(networking_service=networking_service,
                                                   deployment_service=deployment_service)

        # act
        delete_operation.delete_instance(logger=logger,
                                         clients=clients,
                                         kubernetes_name=kubernetes_app_name,
                                         deployed_app_name=deployed_app_name,
                                         namespace=namespace)

        # assert
        networking_service.delete_internal_external_set.assert_called_once_with(logger=logger,
                                                                                clients=clients,
                                                                                service_name_to_delete=kubernetes_app_name,
                                                                                namespace=namespace)
        deployment_service.delete_app(logger=logger,
                                      clients=clients,
                                      namespace=namespace,
                                      app_name_to_delete=kubernetes_app_name)
        deployment_service.wait_until_exists(logger=logger,
                                             clients=clients,
                                             namespace=namespace,
                                             app_name=kubernetes_app_name)

import unittest

from mock import Mock

from domain.operations.power import PowerOperation


class TestPowerOperation(unittest.TestCase):
    def test_power_off(self):
        # arrange
        logger = Mock()
        clients = Mock()
        deployed_app_mock = Mock()

        deployment_service = Mock()
        deployment_mock = Mock()
        deployment_service.get_deployment_by_name = Mock(return_value=deployment_mock)

        power_operation = PowerOperation(deployment_service)

        # act
        power_operation.power_off(logger=logger,
                                  clients=clients,
                                  deployed_app=deployed_app_mock)

        # assert
        self.assertEquals(deployment_mock.spec.replicas, 0)
        deployment_service.update_deployment.assert_called_once_with(
            logger=logger,
            clients=clients,
            namespace=deployed_app_mock.namespace,
            app_name=deployed_app_mock.kubernetes_name,
            updated_deployment=deployment_mock)

    def test_power_on(self):
        # arrange
        logger = Mock()
        clients = Mock()
        deployed_app_mock = Mock()
        deployed_app_mock.wait_for_replicas_to_be_ready = 0

        deployment_mock = Mock()
        deployment_service = Mock()
        deployment_service.get_deployment_by_name = Mock(return_value=deployment_mock)

        power_operation = PowerOperation(deployment_service)

        # act
        power_operation.power_on(logger=logger,
                                 clients=clients,
                                 deployed_app=deployed_app_mock)

        # assert
        self.assertEquals(deployment_mock.spec.replicas, deployed_app_mock.replicas)

        deployment_service.update_deployment.assert_called_once_with(
            logger=logger,
            clients=clients,
            namespace=deployed_app_mock.namespace,
            app_name=deployed_app_mock.kubernetes_name,
            updated_deployment=deployment_mock)

        deployment_service.wait_until_all_replicas_ready.assert_not_called()

    def test_power_on_waits_for_pods_to_be_ready(self):
        # arrange
        logger = Mock()
        clients = Mock()
        deployed_app_mock = Mock()
        deployed_app_mock.wait_for_replicas_to_be_ready = 100

        deployment_mock = Mock()
        deployment_service = Mock()
        deployment_service.get_deployment_by_name = Mock(return_value=deployment_mock)

        power_operation = PowerOperation(deployment_service)

        # act
        power_operation.power_on(logger=logger,
                                 clients=clients,
                                 deployed_app=deployed_app_mock)

        # assert
        self.assertEquals(deployment_mock.spec.replicas, deployed_app_mock.replicas)
        deployment_service.update_deployment.assert_called_once_with(
            logger=logger,
            clients=clients,
            namespace=deployed_app_mock.namespace,
            app_name=deployed_app_mock.kubernetes_name,
            updated_deployment=deployment_mock)

        deployment_service.wait_until_all_replicas_ready.assert_called_once()

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

        deployment_service = Mock()
        deployment_mock = Mock()
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

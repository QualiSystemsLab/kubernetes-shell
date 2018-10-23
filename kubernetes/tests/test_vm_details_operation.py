import unittest

from mock import Mock, MagicMock, patch

from domain.operations.vm_details import VmDetialsOperation


class TestVmDetailsOperation(unittest.TestCase):

    @patch('domain.operations.vm_details.DeployedAppResource')
    def test_create_vm_details_bulk(self, deployed_app_resource_class):
        # arrange
        clients = Mock()
        vm_details_service = Mock()
        deployment_service = Mock()
        networking_service = Mock()
        vm_details_operation = VmDetialsOperation(vm_details_service=vm_details_service,
                                                  deployment_service=deployment_service,
                                                  networking_service=networking_service)
        items = {'items': [MagicMock(), MagicMock()]}

        # act
        results = vm_details_operation.create_vm_details_bulk(logger=Mock(),
                                                              clients=clients,
                                                              items=items)

        # assert
        self.assertEquals(len(results), 2)
        self.assertEquals(vm_details_service.create_vm_details.call_count, 2)

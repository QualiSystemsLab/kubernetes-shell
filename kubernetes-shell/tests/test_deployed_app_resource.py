import unittest

from mock import Mock, patch

from model.deployed_app import DeployedAppResource


class TestDeployedAppResource(unittest.TestCase):
    def setUp(self):
        self.deployed_app_dict = {
            'name': 'deployed_app_name',
            'vmdetails': {
                'uid': 'vm_uid',
                'vmCustomParams': [
                    {'name': 'param1', 'value': 'val1'},
                    {'name': 'namespace', 'value': 'my-sandbox-namespace'},
                    {'name': 'replicas', 'value': '3'},
                    {'name': 'wait_for_replicas_to_be_ready', 'value': '180'},
                ]
            }
        }

    @patch('model.deployed_app.json')
    def test_cloudshell_resource_name_init_from_context(self, json_class):
        # arrange
        json_class.loads = Mock(return_value=self.deployed_app_dict)
        context = Mock()

        # act
        deployed_app = DeployedAppResource(resource_context=context)

        # assert
        json_class.loads.assert_called_once_with(context.app_context.deployed_app_json)
        self.assertEquals(deployed_app.cloudshell_resource_name, 'deployed_app_name')

    def test_cloudshell_resource_name_init_from_dict(self):
        # act
        deployed_app = DeployedAppResource(deployed_app_dict=self.deployed_app_dict)

        # assert
        self.assertEquals(deployed_app.cloudshell_resource_name, 'deployed_app_name')

    @patch('model.deployed_app.json')
    def test_kubernetes_name_init_from_context(self, json_class):
        # arrange
        json_class.loads = Mock(return_value=self.deployed_app_dict)
        context = Mock()

        # act
        deployed_app = DeployedAppResource(resource_context=context)

        # assert
        json_class.loads.assert_called_once_with(context.app_context.deployed_app_json)
        self.assertEquals(deployed_app.kubernetes_name, 'vm_uid')

    def test_kubernetes_name_init_from_dict(self):
        # act
        deployed_app = DeployedAppResource(deployed_app_dict=self.deployed_app_dict)

        # assert
        self.assertEquals(deployed_app.kubernetes_name, 'vm_uid')

    @patch('model.deployed_app.json')
    def test_namespace_init_from_context(self, json_class):
        # arrange
        json_class.loads = Mock(return_value=self.deployed_app_dict)
        context = Mock()

        # act
        deployed_app = DeployedAppResource(resource_context=context)

        # assert
        json_class.loads.assert_called_once_with(context.app_context.deployed_app_json)
        self.assertEquals(deployed_app.namespace, 'my-sandbox-namespace')

    def test_namespace_init_from_dict(self):
        # act
        deployed_app = DeployedAppResource(deployed_app_dict=self.deployed_app_dict)

        # assert
        self.assertEquals(deployed_app.namespace, 'my-sandbox-namespace')

    @patch('model.deployed_app.json')
    def test_replicas_init_from_context(self, json_class):
        # arrange
        json_class.loads = Mock(return_value=self.deployed_app_dict)
        context = Mock()

        # act
        deployed_app = DeployedAppResource(resource_context=context)

        # assert
        json_class.loads.assert_called_once_with(context.app_context.deployed_app_json)
        self.assertEquals(deployed_app.replicas, 3)

    def test_replicas_init_from_dict(self):
        # act
        deployed_app = DeployedAppResource(deployed_app_dict=self.deployed_app_dict)

        # assert
        self.assertEquals(deployed_app.replicas, 3)

    @patch('model.deployed_app.json')
    def test_wait_for_replicas_to_be_ready_init_from_context(self, json_class):
        # arrange
        json_class.loads = Mock(return_value=self.deployed_app_dict)
        context = Mock()

        # act
        deployed_app = DeployedAppResource(resource_context=context)

        # assert
        json_class.loads.assert_called_once_with(context.app_context.deployed_app_json)
        self.assertEquals(deployed_app.wait_for_replicas_to_be_ready, 180)

    def test_wait_for_replicas_to_be_ready_init_from_dict(self):
        # act
        deployed_app = DeployedAppResource(deployed_app_dict=self.deployed_app_dict)

        # assert
        self.assertEquals(deployed_app.wait_for_replicas_to_be_ready, 180)

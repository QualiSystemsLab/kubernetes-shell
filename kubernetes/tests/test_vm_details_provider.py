import unittest

from cloudshell.cp.core.models import VmDetailsProperty
from mock import Mock, MagicMock

from domain.services.vm_details import VmDetailsProvider


class TestVmDetailsProvider(unittest.TestCase):

    def setUp(self):
        self.vm_details_provider = VmDetailsProvider()

    def test_create_vm_details_from_deployment_only(self):
        # arrange
        deployment = MagicMock()
        deployment.spec.template.spec.containers = [Mock(image='ubuntu:16.04'), Mock(image='ubuntu:16.04'), Mock(image='ubuntu:14.04')]

        # act
        result = self.vm_details_provider.create_vm_details([], deployment)

        # assert
        self.assertFalse(result.vmNetworkData)
        self.assertEquals(len(result.vmInstanceData), 7)

        self.assertIn('ubuntu:16.04', self._get_vm_prop(result, 'Image').value)
        self.assertIn('ubuntu:14.04', self._get_vm_prop(result, 'Image').value)
        self.assertEquals(self._get_vm_prop(result, 'Replicas').value, deployment.spec.replicas)
        self.assertEquals(self._get_vm_prop(result, 'Ready Replicas').value, deployment.status.ready_replicas)
        self.assertEquals(self._get_vm_prop(result, 'Internal IP').value, '')
        self.assertEquals(self._get_vm_prop(result, 'Internal Ports').value, '')
        self.assertEquals(self._get_vm_prop(result, 'External IP').value, '')
        self.assertEquals(self._get_vm_prop(result, 'External Ports').value, '')

    def test_create_vm_details_from_deployment_and_services(self):
        # arrange
        deployment = MagicMock()
        deployment.spec.template.spec.containers = [Mock(image='ubuntu:16.04'), Mock(image='ubuntu:16.04'), Mock(image='ubuntu:14.04')]

        internal_service = Mock()
        internal_service.metadata.labels = {'cloudshell-internal-service': True}
        internal_service.spec.ports = [Mock(port=8080), Mock(port=1234), Mock(port=5678)]

        external_service = Mock()
        external_service.metadata.labels = {'cloudshell-external-service': True}
        external_service.spec.ports = [Mock(port=81), Mock(port=82)]

        # act
        result = self.vm_details_provider.create_vm_details([internal_service, external_service], deployment)

        # assert
        self.assertFalse(result.vmNetworkData)
        self.assertEquals(len(result.vmInstanceData), 7)

        self.assertIn('ubuntu:16.04', self._get_vm_prop(result, 'Image').value)
        self.assertIn('ubuntu:14.04', self._get_vm_prop(result, 'Image').value)
        self.assertEquals(self._get_vm_prop(result, 'Replicas').value, deployment.spec.replicas)
        self.assertEquals(self._get_vm_prop(result, 'Ready Replicas').value, deployment.status.ready_replicas)
        self.assertEquals(self._get_vm_prop(result, 'Internal IP').value, internal_service.spec.cluster_ip)
        self.assertEquals(self._get_vm_prop(result, 'Internal Ports').value, '8080, 1234, 5678')
        self.assertEquals(self._get_vm_prop(result, 'External IP').value, '')
        self.assertEquals(self._get_vm_prop(result, 'External Ports').value, '81, 82')

    def test_create_vm_details_from_deployment_and_deployed_app(self):
        # arrange
        deployment = MagicMock()
        deployment.spec.template.spec.containers = [Mock(image='ubuntu:16.04'), Mock(image='ubuntu:16.04'), Mock(image='ubuntu:14.04')]

        deployed_app = Mock()
        deployed_app.replicas = '4'

        # act
        result = self.vm_details_provider.create_vm_details([], deployment, deployed_app=deployed_app)

        # assert
        self.assertFalse(result.vmNetworkData)
        self.assertEquals(len(result.vmInstanceData), 7)

        self.assertIn('ubuntu:16.04', self._get_vm_prop(result, 'Image').value)
        self.assertIn('ubuntu:14.04', self._get_vm_prop(result, 'Image').value)
        self.assertEquals(self._get_vm_prop(result, 'Replicas').value, '4')
        self.assertEquals(self._get_vm_prop(result, 'Ready Replicas').value, deployment.status.ready_replicas)
        # self.assertEquals(self._get_vm_prop(result, 'Internal IP').value, '')
        # self.assertEquals(self._get_vm_prop(result, 'Internal Ports').value, '')
        # self.assertEquals(self._get_vm_prop(result, 'External IP').value, '')
        # self.assertEquals(self._get_vm_prop(result, 'External Ports').value, '')

    def _get_vm_prop(self, result, key):
        return next(iter(filter(lambda x: x.key == key, result.vmInstanceData)), None)

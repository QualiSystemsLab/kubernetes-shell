import unittest

from cloudshell.cp.core.models import PrepareSubnet, PrepareCloudInfra, CreateKeys, PrepareCloudInfraResult, \
    PrepareSubnetActionResult, CreateKeysActionResult
from mock import Mock

from domain.operations.prepare import PrepareSandboxInfraOperation


class TestPrepareOperation(unittest.TestCase):

    def setUp(self):
        self.namespace_service = Mock()
        self.prepare_operation = PrepareSandboxInfraOperation(self.namespace_service)

    def test_validate_single_subnet_mode_raises_error(self):
        # arrange
        action1 = Mock(spec=PrepareSubnet)
        action2 = Mock(spec=PrepareSubnet)

        # act & assert
        with self.assertRaises(ValueError):
            self.prepare_operation._validate_single_subnet_mode([action1, action2])

    def test_validate_single_subnet_mode_passes(self):
        # arrange
        action1 = Mock(spec=PrepareSubnet)

        # act & assert
        self.prepare_operation._validate_single_subnet_mode([action1])

    def test_prepare_creates_new_namespace_and_returns_all_action_results(self):
        # arrange
        prepare_infra_action = Mock(spec=PrepareCloudInfra, actionId=Mock())
        prepare_subnet_action = Mock(spec=PrepareSubnet, actionId=Mock())
        create_keys_action = Mock(spec=CreateKeys, actionId=Mock())

        self.namespace_service.get_single_by_id = Mock(return_value=None)

        # act
        results = self.prepare_operation.prepare(logger=Mock(),
                                                 sandbox_id=Mock(),
                                                 clients=Mock(),
                                                 actions=[prepare_infra_action,
                                                          prepare_subnet_action,
                                                          create_keys_action])

        # assert
        self.namespace_service.create.assert_called_once()
        self.assertEquals(3, len(results))

        prepare_infra_result = self._single(results, lambda x: isinstance(x, PrepareCloudInfraResult))
        self.assertEquals(prepare_infra_result.actionId, prepare_infra_action.actionId)

        prepare_subnet_result = self._single(results, lambda x: isinstance(x, PrepareSubnetActionResult))
        self.assertEquals(prepare_subnet_result.actionId, prepare_subnet_action.actionId)

        create_keys_result = self._single(results, lambda x: isinstance(x, CreateKeysActionResult))
        self.assertEquals(create_keys_result.actionId, create_keys_action.actionId)

    def test_prepare_when_namespace_exists(self):
        # arrange
        prepare_infra_action = Mock(spec=PrepareCloudInfra, actionId=Mock())
        prepare_subnet_action = Mock(spec=PrepareSubnet, actionId=Mock())
        create_keys_action = Mock(spec=CreateKeys, actionId=Mock())

        namespace_obj_mock = Mock()
        self.namespace_service.get_single_by_id = Mock(return_value=namespace_obj_mock)

        # act
        results = self.prepare_operation.prepare(logger=Mock(),
                                                 sandbox_id=Mock(),
                                                 clients=Mock(),
                                                 actions=[prepare_infra_action,
                                                          prepare_subnet_action,
                                                          create_keys_action])

        # assert
        self.namespace_service.create.assert_not_called()
        self.assertEquals(3, len(results))

        prepare_infra_result = self._single(results, lambda x: isinstance(x, PrepareCloudInfraResult))
        self.assertEquals(prepare_infra_result.actionId, prepare_infra_action.actionId)

        prepare_subnet_result = self._single(results, lambda x: isinstance(x, PrepareSubnetActionResult))
        self.assertEquals(prepare_subnet_result.actionId, prepare_subnet_action.actionId)

        create_keys_result = self._single(results, lambda x: isinstance(x, CreateKeysActionResult))
        self.assertEquals(create_keys_result.actionId, create_keys_action.actionId)

    @staticmethod
    def _single(lst, predicate):
        return filter(predicate, lst)[0]

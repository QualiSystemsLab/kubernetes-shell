import unittest

from mock import Mock

from domain.services.clients import ApiClientsProvider


class TestApiClientProvider(unittest.TestCase):

    def test_get_api_clients_raises_when_file_not_exist(self):
        # arrange
        clp_mock = Mock(config_file_path='c:\\some_file_path')
        provider = ApiClientsProvider()

        # act & assert
        with self.assertRaisesRegexp(ValueError, "Config File Path is invalid. Cannot open file '.+'"):
            provider.get_api_clients(clp_mock)
import unittest

from domain.common.utils import convert_to_int_list, convert_app_name_to_valide_kubernetes_name


class TestUtils(unittest.TestCase):

    def test_convert_to_int_list(self):
        # arrange
        comma_separeted_str = '1, 2,5'

        # act
        result = convert_to_int_list(comma_separeted_str)

        # assert
        self.assertListEqual(result, [1, 2, 5])

    def test_convert_app_name_to_valide_kubernetes_name(self):
        # arrange
        app_name = 'Kube Test'

        # act
        result = convert_app_name_to_valide_kubernetes_name(app_name)

        # assert
        self.assertEqual(result, 'kube-test')
import json
import unittest
from unittest import mock
from src.lib.mgn_launch_configuration import MGNLaunchConfig


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        with open("data/boto3_api_responses/mgn_get_launch_configuration_response.json") as f:
            self._mgn_launch_config_json = json.load(f)
        self._mock_client = mock.Mock()
        self._mock_client.get_launch_configuration.return_value = self._mgn_launch_config_json

    @mock.patch('boto3.client')
    def test_properties_getter(self, mock_boto3_client):
        mock_boto3_client.return_value = self._mock_client
        mgn_lc = MGNLaunchConfig(self._mgn_launch_config_json['sourceServerID'])
        self.assertTrue(mock_boto3_client.called)
        self.assertEqual(mgn_lc.launch_template_id, "lt-01d047bef6f39c92c")
        self.assertEqual(mgn_lc.launch_disposition, "STARTED")
        self.assertFalse(mgn_lc.copy_tags)
        self.assertFalse(mgn_lc.copy_private_ip)
        self.assertFalse(mgn_lc.byol)
        self.assertEqual(mgn_lc.instance_right_sizing_method, "NONE")


if __name__ == '__main__':
    unittest.main()

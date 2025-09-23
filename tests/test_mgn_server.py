import json
import unittest
from unittest import mock
from src.lib.mgn_server import MGNServer


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        with open("data/boto3_api_responses/mgn_get_launch_configuration_response.json") as f:
            self._mgn_launch_config_json = json.load(f)
        with open("data/boto3_api_responses/mgn_describe_source_servers_response.json") as f:
            self._mgn_describe_source_servers = json.load(f)
        self._mock_client = mock.Mock()
        self._mock_client.get_launch_configuration.return_value = self._mgn_launch_config_json
        self._mock_client.describe_source_servers.return_value = self._mgn_describe_source_servers

    @mock.patch('boto3.client')
    @mock.patch('src.lib.mgn_launch_configuration.MGNLaunchConfig')
    @mock.patch('src.lib.ec2_launch_template.EC2LaunchTemplate')
    def test_properties_getter(self, mock_lt, mock_lc, mock_boto3_client):
        mock_boto3_client.return_value = self._mock_client
        mock_lc.return_value = mock.Mock()
        mock_lt.return_value = mock.Mock()
        srv = MGNServer(self._mgn_describe_source_servers.get('items')[0].get('sourceServerID'))
        self.assertEqual(srv.on_prem_name, self._mgn_describe_source_servers.get('items')[0].get('tags').get('Name'))
        self.assertEqual(srv.life_cycle_state, self._mgn_describe_source_servers.get('items')[0].get('lifeCycle', {}).get('state', ""))
        self.assertTrue(mock_lc.called)
        self.assertEqual(mock_lc.call_args.args[0], srv.source_server_id)
        self.assertTrue(mock_lt.called)
        self.assertEqual(mock_lt.call_args.args[0], self._mgn_launch_config_json.get('ec2LaunchTemplateID'))


if __name__ == '__main__':
    unittest.main()

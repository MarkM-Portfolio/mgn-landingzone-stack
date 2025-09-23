import json
import unittest
from unittest import mock
from src.lib.ec2_launch_template import EC2LaunchTemplate

class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        with open("data/boto3_api_responses/ec2_describe_launch_template_response.json") as f:
            self._ec2_launch_template_json = json.load(f)
        with open("data/boto3_api_responses/ec2_describe_launch_template_version_response.json") as f:
            self._ec2_launch_template_version_json = json.load(f)
        with open("data/boto3_api_responses/ec2_create_launch_template_version_response.json") as f:
            self._ec2_create_lt_version_json = json.load(f)
        self._ec2_launch_template_data_dict = self._ec2_launch_template_version_json.get("LaunchTemplateVersions")[0].get("LaunchTemplateData")
        self._mock_client = mock.Mock()
        self._mock_client.describe_launch_templates.return_value = self._ec2_launch_template_json
        self._mock_client.describe_launch_template_versions.return_value = self._ec2_launch_template_version_json
        self._mock_client.create_launch_template_version.return_value = self._ec2_create_lt_version_json
        self._mock_client.modify_launch_template.return_value = {}

    @mock.patch('boto3.client')
    def test_constructor_should_use_boto3_apis(self, mock_boto3_client) -> None:
        mock_boto3_client.return_value = self._mock_client
        EC2LaunchTemplate(self._ec2_launch_template_json.get('LaunchTemplateId'))
        self.assertTrue(self._mock_client.describe_launch_templates.called)
        self.assertTrue(self._mock_client.describe_launch_template_versions.called)

    @mock.patch('boto3.client')
    def test_properties_getter(self, mock_boto3_client) -> None:
        mock_boto3_client.return_value = self._mock_client
        lt = EC2LaunchTemplate(self._ec2_launch_template_json.get('LaunchTemplateId'))
        self.assertEqual(lt.default_version, str(self._ec2_launch_template_json.get("LaunchTemplates")[0].get('DefaultVersionNumber')))
        self.assertEqual(lt.default_version, str(self._ec2_launch_template_json.get("LaunchTemplates")[0].get('LatestVersionNumber')))
        self.assertEqual(lt.instance_type, self._ec2_launch_template_data_dict['InstanceType'])
        self.assertEqual(lt.vpc_subnet_id, self._ec2_launch_template_data_dict.get("NetworkInterfaces")[0].get("SubnetId"))

    @mock.patch('boto3.client')
    def test_update_lt_settings_should_call_boto3_api(self, mock_boto3_client) -> None:
        mock_boto3_client.return_value = self._mock_client
        lt = EC2LaunchTemplate(self._ec2_launch_template_json.get('LaunchTemplateId'))
        lt.update_settings()
        self.assertTrue(self._mock_client.create_launch_template_version.called)
        self.assertEqual(self._mock_client.create_launch_template_version.call_args_list[0].kwargs['SourceVersion'], '7')
        self.assertEqual(self._mock_client.create_launch_template_version.call_args_list[0].kwargs['LaunchTemplateData'], self._ec2_launch_template_data_dict)

    @mock.patch('boto3.client')
    def test_update_lt_settings_should_update_default_version(self, mock_boto3_client) -> None:
        mock_boto3_client.return_value = self._mock_client
        lt = EC2LaunchTemplate(self._ec2_launch_template_json.get('LaunchTemplateId'))
        lt.update_settings()
        self.assertTrue(self._mock_client.modify_launch_template.called)
        self.assertEqual(self._mock_client.modify_launch_template.call_args_list[0].kwargs['LaunchTemplateId'], self._ec2_launch_template_json.get('LaunchTemplateId'))
        self.assertEqual(self._mock_client.modify_launch_template.call_args_list[0].kwargs['DefaultVersion'], str(self._ec2_create_lt_version_json.get('LaunchTemplateVersion').get('VersionNumber')))
        self.assertEqual(self._mock_client.describe_launch_templates.call_count, 2)
        self.assertEqual(self._mock_client.describe_launch_template_versions.call_count, 2)


if __name__ == '__main__':
    unittest.main()

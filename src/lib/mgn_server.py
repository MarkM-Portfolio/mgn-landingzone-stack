import boto3
import src.lib.mgn_launch_configuration as lc
import src.lib.ec2_launch_template as lt

class MGNServer:
    @staticmethod
    def get_source_server_ids() -> list:
        filters = {'isArchived': False}
        client = boto3.client('mgn')
        return [item.get("sourceServerID", "") for item in client.describe_source_servers(filters=filters).get('items', [])]

    def __init__(self, source_server_id: str):
        self._client = boto3.client('mgn')
        self._source_server_id = source_server_id
        self._launch_configuration = lc.MGNLaunchConfig(source_server_id)
        self._ec2_launch_template = lt.EC2LaunchTemplate(self._get_ec2_launch_template_id())
        self._source_server_json_description = self._client.describe_source_servers(filters={'sourceServerIDs': [source_server_id]})

    @property
    def source_server_id(self):
        return self._source_server_id

    @property
    def launch_template_id(self):
        return self._launch_configuration.launch_template_id

    @property
    def on_prem_name(self):
        return self._source_server_json_description.get('items')[0].get('tags').get('Name')

    @property
    def launch_config_setting(self):
        return self._launch_configuration

    @property
    def ec2_launch_template(self):
        return self._ec2_launch_template

    @property
    def life_cycle_state(self):
        return self._source_server_json_description.get('items')[0].get('lifeCycle', {}).get('state', "")

    def update_launch_config(self, copy_tags: bool = False, launch_disposition: str = "STARTED", right_sizing: str = "NONE"):
        self._launch_configuration.copy_tags = copy_tags
        self._launch_configuration.launch_disposition = launch_disposition
        self._launch_configuration.instance_right_sizing_method = right_sizing
        self._launch_configuration.update_settings()

    def _get_ec2_launch_template_id(self):
        return self._client.get_launch_configuration(sourceServerID=self._source_server_id).get('ec2LaunchTemplateID')

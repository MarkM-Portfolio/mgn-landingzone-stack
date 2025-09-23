import boto3


class MGNLaunchConfig:
    def __init__(self, source_server: str):
        self._client = boto3.client('mgn')
        self._config_settings = self._client.get_launch_configuration(sourceServerID=source_server)
        self._mgn_source_server_id = source_server

    @property
    def copy_private_ip(self):
        return self._config_settings['copyPrivateIp']

    @copy_private_ip.setter
    def copy_private_ip(self, value: bool):
        self._config_settings['copyPrivateIp'] = value

    @property
    def copy_tags(self):
        return self._config_settings['copyTags']

    @copy_tags.setter
    def copy_tags(self, value: bool):
        self._config_settings['copyTags'] = value

    @property
    def launch_template_id(self):
        return self._config_settings['ec2LaunchTemplateID']

    @property
    def launch_disposition(self):
        return self._config_settings['launchDisposition']

    @launch_disposition.setter
    def launch_disposition(self, value: str) -> None:
        self._config_settings['launchDisposition'] = value

    @property
    def byol(self):
        return self._config_settings['licensing']['osByol']

    @property
    def instance_right_sizing_method(self):
        return self._config_settings['targetInstanceTypeRightSizingMethod']

    @instance_right_sizing_method.setter
    def instance_right_sizing_method(self, value) -> None:
        self._config_settings['targetInstanceTypeRightSizingMethod'] = value

    def disable_instance_startup_on_launch(self) -> None:
        self._config_settings['launchDisposition'] = "STOPPED"

    def enable_instance_startup_on_launch(self) -> None:
        self._config_settings['launchDisposition'] = "STARTED"

    def disable_instance_right_sizing(self) -> None:
        self._config_settings['targetInstanceTypeRightSizingMethod'] = "NONE"

    def enable_instance_right_sizing(self) -> None:
        self._config_settings['targetInstanceTypeRightSizingMethod'] = "BASIC"

    def update_settings(self) -> dict:
        return self._client.update_launch_configuration(copyTags=self.copy_tags,
                                                        launchDisposition=self.launch_disposition,
                                                        targetInstanceTypeRightSizingMethod=self.instance_right_sizing_method,
                                                        sourceServerID=self._mgn_source_server_id)

import boto3

class EC2LaunchTemplate:
    def __init__(self, launch_template_id: str):
        self._launch_template_id = launch_template_id
        self._client = boto3.client("ec2")
        self._template_json = self._get_launch_template_details()
        self._template_data = self._get_launch_template_details_by_version()

    def update_settings(self):
        resp = self._client.create_launch_template_version(LaunchTemplateId=self._launch_template_id,
                                                           SourceVersion=str(self.default_version),
                                                           LaunchTemplateData=self._template_data)
        self.set_default_version(str(resp.get('LaunchTemplateVersion').get('VersionNumber')))
        self._template_json = self._get_launch_template_details()
        self._template_data = self._get_launch_template_details_by_version()

    def set_default_version(self, version_number: str):
        self._client.modify_launch_template(LaunchTemplateId=self._launch_template_id, DefaultVersion=version_number)

    @property
    def latest_version(self):
        return str(self._template_json.get("LaunchTemplates")[0].get("LatestVersionNumber"))

    @property
    def default_version(self) -> str:
        return str(self._template_json.get("LaunchTemplates")[0].get("DefaultVersionNumber"))

    @default_version.setter
    def default_version(self, version: str) -> None:
        self.set_default_version(version)

    @property
    def iam_instance_profile_arn(self) -> str:
        return self._template_data.get("IamInstanceProfile", {}).get("Arn", "")

    @iam_instance_profile_arn.setter
    def iam_instance_profile_arn(self, value: str) -> None:
        if "IamInstanceProfile" not in self._template_data:
            self._template_data["IamInstanceProfile"] = {}
        self._template_data["IamInstanceProfile"]["Arn"] = value

    @property
    def instance_type(self) -> str:
        return self._template_data.get("InstanceType")

    @instance_type.setter
    def instance_type(self, value: str) -> None:
        self._template_data["InstanceType"] = value

    @property
    def vpc_subnet_id(self) -> str:
        return self._template_data.get("NetworkInterfaces")[0].get("SubnetId")

    @vpc_subnet_id.setter
    def vpc_subnet_id(self, value: str):
        self._template_data["NetworkInterfaces"][0]["SubnetId"] = value

    @property
    def vpc_security_groups_id(self) -> list:
        return self._template_data.get("NetworkInterfaces")[0].get("Groups")

    @vpc_security_groups_id.setter
    def vpc_security_groups_id(self, value: list) -> None:
        self._template_data["NetworkInterfaces"][0]["Groups"] = value

    @property
    def ebs_storage_iops(self):
        for index, ebs_volume in enumerate(self._template_data['BlockDeviceMappings']):
            if "Ebs" not in self._template_data['BlockDeviceMappings'][index]:
                continue
            return self._template_data['BlockDeviceMappings'][index]["Ebs"].get("Iops", "")

    @ebs_storage_iops.setter
    def ebs_storage_iops(self, value: int):
        for index, ebs_volume in enumerate(self._template_data['BlockDeviceMappings']):
            if "Ebs" not in self._template_data['BlockDeviceMappings'][index]:
                continue
            self._template_data['BlockDeviceMappings'][index]["Ebs"]["Iops"] = value

    @property
    def ebs_storage_type(self):
        for index, ebs_volume in enumerate(self._template_data['BlockDeviceMappings']):
            if "Ebs" not in self._template_data['BlockDeviceMappings'][index]:
                continue
            return self._template_data['BlockDeviceMappings'][index]["Ebs"]["VolumeType"]

    @ebs_storage_type.setter
    def ebs_storage_type(self, value: str):
        for index, ebs_volume in enumerate(self._template_data['BlockDeviceMappings']):
            if "Ebs" not in self._template_data['BlockDeviceMappings'][index]:
                continue
            self._template_data['BlockDeviceMappings'][index]["Ebs"]["VolumeType"] = value

    def _get_launch_template_details(self):
        return self._client.describe_launch_templates(LaunchTemplateIds=[self._launch_template_id])

    def _get_launch_template_details_by_version(self):
        resp = self._client.describe_launch_template_versions(Versions=[str(self.default_version)],
                                                              LaunchTemplateId=self._launch_template_id)
        return resp.get("LaunchTemplateVersions")[0].get("LaunchTemplateData")

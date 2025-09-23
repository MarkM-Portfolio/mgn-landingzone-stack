import json
import boto3

client = boto3.client('mgn')
def main():
    if not is_mgn_service_initialized():
        create_mgn_roles()
        client.initialize_service()
        create_replication_template()
        create_mgn_iam_user()

def is_mgn_service_initialized() -> bool:
    try:
        client.describe_replication_configuration_templates(replicationConfigurationTemplateIDs=[])
    except client.exceptions.UninitializedAccountException:
        return False
    return True

def get_replication_template():
    return client.describe_replication_configuration_templates(replicationConfigurationTemplateIDs=[])

def create_replication_template():
    client.create_replication_configuration_template(
        associateDefaultSecurityGroup=True,
        bandwidthThrottling=0,
        createPublicIP=False,
        dataPlaneRouting='PRIVATE_IP',
        defaultLargeStagingDiskType='GP3',
        ebsEncryption='DEFAULT',
        replicationServerInstanceType='t3.small',
        replicationServersSecurityGroupsIDs=[],
        stagingAreaSubnetId=get_staging_area_subnet_id(),
        stagingAreaTags={},
        useDedicatedReplicationServer=False
    )

def get_staging_area_subnet_id() -> str:
    ec2_client = boto3.client('ec2')
    res = boto3.resource('ec2')
    resp = ec2_client.describe_vpcs()
    vpc = res.Vpc(resp.get('Vpcs')[0].get('VpcId'))
    subnet_id: str = ""

    for subnet in vpc.subnets.all():
        subnet_name = [tag.get('Value') for tag in subnet.tags if tag.get('Key') == "Name"][0]
        if "data" in subnet_name:
            subnet_id = subnet.subnet_id
            break
    return subnet_id

def create_mgn_iam_user():
    mgn_iam_user_name = "MGNUser"
    boto3.client('iam').create_user(UserName=mgn_iam_user_name)
    mgn_user = boto3.resource('iam').User(mgn_iam_user_name)
    mgn_user.attach_policy(PolicyArn='arn:aws:iam::aws:policy/AWSApplicationMigrationAgentPolicy')

def create_mgn_roles():
    assume_role_policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    iam_client = boto3.client('iam')
    iam_resource = boto3.resource('iam')
    for role_name in ["AWSApplicationMigrationReplicationServerRole", "AWSApplicationMigrationConversionServerRole", "AWSApplicationMigrationMGHRole"]:
        try:
            iam_client.create_role(Path='/service-role/', RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy))
        except iam_client.exceptions.EntityAlreadyExistsException:
            continue
    iam_resource.Role("AWSApplicationMigrationReplicationServerRole").attach_policy(PolicyArn="arn:aws:iam::aws:policy/service-role/AWSApplicationMigrationReplicationServerPolicy")
    iam_resource.Role("AWSApplicationMigrationConversionServerRole").attach_policy(PolicyArn="arn:aws:iam::aws:policy/service-role/AWSApplicationMigrationConversionServerPolicy")
    iam_resource.Role("AWSApplicationMigrationMGHRole").attach_policy(PolicyArn="arn:aws:iam::aws:policy/service-role/AWSApplicationMigrationMGHAccess")


if __name__ == "__main__":
    main()

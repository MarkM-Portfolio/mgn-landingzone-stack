import sys

import boto3
import pandas as pd
pd.options.mode.chained_assignment = None
get_region = boto3.session.Session().region_name

def get_aws_account_id() -> str:
    return boto3.client('sts').get_caller_identity().get('Account')

def parse_infra_manifest(runbook_path: str) -> dict:
    subnet_lookup_dict = get_subnets()
    manifest_df = pd.read_excel(runbook_path, sheet_name="Infrastructure Manifest", skiprows=9, usecols="B:X")
    reduced_df = manifest_df[['On-prem Name', 'Migration Path', 'Cloud Name', 'EC2 Instance Type', 'Target Subnet']]
    rehost_df = reduced_df[reduced_df['Migration Path'] == "Rehost"]
    for subnet in subnet_lookup_dict.keys():
        rehost_df['Target Subnet'].replace(subnet, subnet_lookup_dict[subnet], inplace=True)
    rehost_df.columns = ['on_prem_name', 'migration_path', 'target_name', 'instance_type', 'subnet_id']
    return rehost_df.set_index('on_prem_name').T.to_dict()

def get_subnets():
    client = boto3.client('ec2')
    resp = client.describe_vpcs()
    vpc = boto3.resource('ec2').Vpc(resp.get('Vpcs')[0].get('VpcId'))
    subnets = {}

    for subnet in vpc.subnets.all():
        subnet_name = [tag.get('Value') for tag in subnet.tags if tag.get('Key') == "Name"][0]
        customer_name = [tag.get('Value') for tag in subnet.tags if tag.get('Key') == "CustomerName"][0]
        target_subnet = subnet_name.replace(customer_name, '')
        subnet_lookup_name = f"{target_subnet.split('-')[-2].title()} Subnet - {subnet.availability_zone[-1].upper()}"
        subnets[subnet_lookup_name] = subnet.subnet_id
    return subnets

def get_cutover_test_sg_id() -> list:
    sg_ids = []
    for sg in boto3.client('ec2').describe_security_groups().get('SecurityGroups', []):
        if sg.get('GroupName', "").startswith(get_region + "-cutover-test-sg"):
            sg_ids.append(sg.get('GroupId'))
    return sg_ids

def populate_ssm_parameter_store(runbook_path: str):
    """
    retrieves the rehost configuration from the runbook (Infrastructure Manifest) sheet
    and uploads information to Parameter Store (sample structure in SSM Parameter Store)
    /GEN2KTBRK01/instance-type
    /GEN2KTBRK01/instance-name
    /GEN2KTBRK01/vpc-subnet-id
    """
    client = boto3.client('ssm')
    rehost_manifest = parse_infra_manifest(runbook_path)
    for server in rehost_manifest.keys():
        launch_settings = rehost_manifest.get(server)
        client.put_parameter(Name=f'/{server.upper()}/instance-type', Description='', Type='String', Value=launch_settings.get('instance_type'))
        client.put_parameter(Name=f'/{server.upper()}/instance-name', Description='', Type='String', Value=launch_settings.get('target_name'))
        client.put_parameter(Name=f'/{server.upper()}/vpc-subnet-id', Description='', Type='String', Value=launch_settings.get('subnet_id'))
        client.put_parameter(Name=f'/{server.upper()}/vpc-security-groups', Description='', Type='String', Value=",".join(get_cutover_test_sg_id()))
        client.put_parameter(Name=f'/{server.upper()}/ec2-instance-profile', Description='', Type='String', Value=f"arn:aws:iam::{get_aws_account_id()}:instance-profile/SSMInstanceProfile", Overwrite=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        runbook_path = sys.argv[1]
        populate_ssm_parameter_store(sys.argv[1])
    else:
        print("please specify path to the runbook")

import boto3

try:
    from src.lib.mgn_server import MGNServer
except ImportError:
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.lib.mgn_server import MGNServer
    
get_region = boto3.session.Session().region_name

def main():
    client = boto3.client('mgn')
    sec_grps = get_security_groups()

    for server in [item.get("sourceServerID", "") for item in client.describe_source_servers(filters={'lifeCycleStates': ['READY_FOR_CUTOVER']}).get('items', [])]:
        cutover_sec_grps = []
        mgn = MGNServer(server)
        subnet_id = get_value_from_ssm_parameter_store(mgn.on_prem_name, "vpc-subnet-id")
        mgn.launch_config_setting.instance_type = get_value_from_ssm_parameter_store(mgn.on_prem_name, "instance-type")
        mgn.launch_config_setting.vpc_subnet_id = subnet_id
        cutover_sec_grps.append(sec_grps[subnet_id])
        cutover_sec_grps.append(sec_grps['migration'])
        mgn.ec2_launch_template.iam_instance_profile_arn = get_value_from_ssm_parameter_store(mgn.on_prem_name, "ec2-instance-profile")
        mgn.ec2_launch_template.vpc_security_groups_id = cutover_sec_grps
        mgn.ec2_launch_template.ebs_storage_type = "gp3"
        mgn.ec2_launch_template.ebs_storage_iops = 3000
        mgn.ec2_launch_template.update_settings()

def get_value_from_ssm_parameter_store(server_name: str, parameter: str) -> str:
    param = boto3.client('ssm').get_parameter(Name=f'/{server_name.upper()}/{parameter}')
    return param.get('Parameter', {}).get('Value', '')

def get_security_groups():
    sg_ids = {}
    subnets = get_subnets()
    for sg in boto3.client('ec2').describe_security_groups().get('SecurityGroups', []):
        group_name = sg.get('GroupName', "")
        if group_name.startswith(get_region + "-baseline"):
            sg_type = group_name.split('-')[4]
            for subnet in subnets[sg_type]:
                sg_ids[subnet] = sg.get('GroupId')
        elif group_name.startswith(get_region + "-migration-sg"):
            sg_ids['migration'] = sg.get('GroupId')
    return sg_ids

def get_subnets():
    client = boto3.client('ec2')
    resp = client.describe_vpcs()
    vpc = boto3.resource('ec2').Vpc(resp.get('Vpcs')[0].get('VpcId'))
    subnets = {}

    for subnet in vpc.subnets.all():
        subnet_name = [tag.get('Value') for tag in subnet.tags if tag.get('Key') == "Name"][0]
        customer_name = [tag.get('Value') for tag in subnet.tags if tag.get('Key') == "CustomerName"][0]
        target_subnet = subnet_name.replace(customer_name, '')
        subnet_type = target_subnet.split('-')[-2]
        if subnet_type not in subnets:
            subnets[subnet_type] = []
        subnets[subnet_type].append(subnet.subnet_id)
    return subnets


if __name__ == "__main__":
    main()

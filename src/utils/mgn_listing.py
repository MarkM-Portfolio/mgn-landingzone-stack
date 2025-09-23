from tabulate import tabulate
try:
    from src.lib.mgn_server import MGNServer
except ImportError:
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.lib.mgn_server import MGNServer


def main():
    server_details = []
    mgn_source_servers = MGNServer.get_source_server_ids()
    for source_server_id in mgn_source_servers:
        server = MGNServer(source_server_id)
        server_details.append({
            'name': server.on_prem_name ,
            'aws_id': source_server_id,
            'life_cycle': server.life_cycle_state,
            'launch_template_id': server.launch_template_id,
            'default_version': server.ec2_launch_template.default_version,
            'latest_version': server.ec2_launch_template.latest_version,
            'instance_profile': server.ec2_launch_template.iam_instance_profile_arn,
            'instance_type': server.ec2_launch_template.instance_type,
            'volume_type': server.ec2_launch_template.ebs_storage_type,
            'volume_iops': server.ec2_launch_template.ebs_storage_iops,
            'security_groups': server.ec2_launch_template.vpc_security_groups_id
        })
    return server_details


if __name__ == "__main__":
    print(tabulate(main(), showindex="always", headers="keys", tablefmt="orgtbl"))

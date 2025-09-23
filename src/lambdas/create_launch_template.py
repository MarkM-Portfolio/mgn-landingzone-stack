import json
import logging
import sys
import traceback
from pathlib import Path
import boto3
try:
    from src.lib.mgn_server import MGNServer
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.lib.mgn_server import MGNServer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

get_region = boto3.session.Session().region_name

# noinspection PyUnusedLocal,PyBroadException
def lambda_handler(event, context):
    logger.info(f'event received: {event}')
    for source_server in event.get("resources", []):
        try:
            aws_id = source_server.split(":")[-1].split("/")[-1]
            server = MGNServer(aws_id)
            logger.info(f"server {aws_id} {server.on_prem_name} entered state {event.get('detail', {}).get('state', '')}")
            logger.info(f"ec2 launch template ID: {server.launch_template_id}")
            logger.info(f"ec2 launch template default version: {server.ec2_launch_template.default_version}")
            server.update_launch_config()
            _update_ec2_launch_template_settings(server)
        except Exception:
            exception_type, exception_value, exception_traceback = sys.exc_info()
            traceback_string = traceback.format_exception(exception_type, exception_value, exception_traceback)
            err_msg = json.dumps({
                "errorType": exception_type.__name__,
                "errorMessage": str(exception_value),
                "stack_trace": traceback_string
            })
            logger.error(err_msg)

def get_value_from_ssm_parameter_store(server_name: str, parameter: str) -> str:
    param = boto3.client('ssm').get_parameter(Name=f'/{server_name.upper()}/{parameter}')
    logger.debug(f"received from parameter store: {param}")
    return param.get('Parameter', {}).get('Value', '')

def _update_ec2_launch_template_settings(server: MGNServer):
    server.ec2_launch_template.instance_type = get_value_from_ssm_parameter_store(server.on_prem_name, "instance-type")
    server.ec2_launch_template.vpc_subnet_id = get_value_from_ssm_parameter_store(server.on_prem_name, "vpc-subnet-id")
    server.ec2_launch_template.iam_instance_profile_arn = get_value_from_ssm_parameter_store(server.on_prem_name, "ec2-instance-profile")
    server.ec2_launch_template.vpc_security_groups_id = get_value_from_ssm_parameter_store(server.on_prem_name, "vpc-security-groups").split(",")
    server.ec2_launch_template.ebs_storage_type = "gp3"
    server.ec2_launch_template.ebs_storage_iops = 3000
    server.ec2_launch_template.update_settings()


if __name__ == "__main__":
    module_root = str(Path(__file__).parent.parent.parent)
    with open(f"{module_root}/tests/data/event_files/mgn_source_server_ready_for_test_event.json") as event_file:
        event_data = json.load(event_file)
        event_data["resources"].clear()
        for srv in MGNServer.get_source_server_ids():
            event_data["resources"].append("arn:aws:mgn:{region}:708136847608:source-server/{srv}".format(region=get_region,srv=srv))
        lambda_handler(event_data, {})

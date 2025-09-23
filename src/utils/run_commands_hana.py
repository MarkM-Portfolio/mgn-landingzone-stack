#!/usr/bin/python

# Script to Run SSM Commands for HANA box
# Syntax for command-
# python run_commands.py -i i-12345678,i-87654321,i-xxxxxxxxxx,etc -r region

import boto3
import argparse
import os
import json
import time
import logging
import sys

logFormatter = '%(asctime)s - %(message)s'
logging.basicConfig(format=logFormatter, level=logging.INFO)
logger = logging.getLogger(__name__)

get_region = boto3.session.Session().region_name

def _configure():
    parser = argparse.ArgumentParser(description=['Insert the ID of the Target Instance'])
    parser.add_argument('-i','--instance-id', help='Target Instance ID', nargs='?', dest="instanceid")
    parser.add_argument('-r','--region', help='Target Region', nargs='?', dest="region", default=get_region)
    args = vars(parser.parse_args())

    instance_ids = [str(item) for item in args["instanceid"].split(',')]
    region = args["region"]

    return instance_ids, region


def main(instance_ids, region):

    session = boto3.session.Session()
    ssm_client = session.client('ssm')

    ssm_document_names = [
        "AWS-ConfigureAWSPackage",
        "AmazonCloudWatch-ManageAgent",
        "AWS-UpdateSSMAgent",
    ]

    ssm_config_packages = [
        "AmazonCloudWatchAgent"
    ]

    for instance_id in instance_ids:
        logger.info(f"Target '{instance_id}'")
    for document_name in ssm_document_names:
        if document_name == "AWS-UpdateSSMAgent":
            logger.info(f"Initiating {document_name} on target(s)")

            try: 
                send_command_response = ssm_client.send_command(
                    InstanceIds=instance_ids,
                    DocumentName=document_name,
                    TimeoutSeconds=120,
                    Comment=f"Running {document_name}"
                )

            except ssm_client.exceptions.InternalServerError:
                logger.info("Error: Internal Server Error")
                sys.exit(1)
            except ssm_client.exceptions.InvalidInstanceId:
                logger.info("Error: Invalid Instance ID")
                sys.exit(1)
            except ssm_client.exceptions.InvalidRole:
                logger.info("Error: Invalid Role")
                sys.exit(1)

            time.sleep(2)
            for instance_id in instance_ids:
                if document_name == "AWS-UpdateSSMAgent":
                    time.sleep(5)
                    command_wait(ssm_client, send_command_response["Command"]["CommandId"], instance_id)
                else:
                    logger.info(f"Specify the PluginName for document {document_name}")
                
        if document_name == "AmazonCloudWatch-ManageAgent":
            logger.info(f"Initiating {document_name} on target(s)")

            try: 
                send_command_response = ssm_client.send_command(
                  InstanceIds=instance_ids,
                  DocumentName=document_name,
                  Parameters={
                      'action': [
                          'configure',
                      ],
                      'mode': [
                          'ec2',
                      ],
                      'optionalConfigurationLocation': [
                          "default",
                      ],
                      'optionalConfigurationSource': [
                          'default',
                      ],  
                      'optionalRestart': [
                          'yes',
                      ],
                  },
                  TimeoutSeconds=120,
                  Comment=f"Running {document_name}"
                )
            except ssm_client.exceptions.InternalServerError:
                logger.info("Error: Internal Server Error")
                sys.exit(1)
            except ssm_client.exceptions.InvalidInstanceId:
                logger.info("Error: Invalid Instance ID")
                sys.exit(1)
            except ssm_client.exceptions.InvalidRole:
                logger.info("Error: Invalid Role")
                sys.exit(1)

            for instance_id in instance_ids:
                time.sleep(2)
                command_wait(ssm_client, send_command_response["Command"]["CommandId"], instance_id)
                       
        if document_name == "AWS-ConfigureAWSPackage":
            for package in ssm_config_packages:
                logger.info(f"Initiating {document_name} {package} on target(s)")
                try:
                    send_command_response = ssm_client.send_command(
                        InstanceIds=instance_ids,
                        DocumentName=document_name,
                        Parameters={
                            'action': [
                                'Install',
                            ],
                            'installationType': [
                                'Uninstall and reinstall',
                            ],
                            'name': [
                                package,
                            ],
                            'version': [
                                ''
                            ]
                        },
                        TimeoutSeconds=120,
                        Comment=f"Running {document_name}",
                    )
                except ssm_client.exceptions.InternalServerError:
                    logger.info("Error: Internal Server Error")
                    sys.exit(1)
                except ssm_client.exceptions.InvalidInstanceId:
                    logger.info("Error: Invalid Instance ID")
                    sys.exit(1)
                except ssm_client.exceptions.InvalidRole:
                    logger.info("Error: Invalid Role")
                    sys.exit(1)

                time.sleep(2)
                for instance_id in instance_ids:
                    command_wait(ssm_client, send_command_response["Command"]["CommandId"], instance_id)

    logger.info("End of Script")

def command_wait(ssm_client, command_id, instance_id):

    get_command_response = ""

    while True:
        try:
            get_command_response = ssm_client.get_command_invocation(
                CommandId=str(command_id),
                InstanceId=str(instance_id),
            )
        except ssm_client.exceptions.InternalServerError:
            logger.info("Error: Internal Server Error")
        except ssm_client.exceptions.InvalidInstanceId:
            logger.info("Error: Invalid Instance ID")
        except ssm_client.exceptions.InvocationDoesNotExist:
            logger.info("Error: Invocation does not Exist")
        if get_command_response["Status"] == "Success":
            logger.info(f"Status: Success {instance_id}")
            break
        elif get_command_response["Status"] == "Failed":
            logger.info(f"Status: Failed {instance_id} ")
            sys.exit(1)
        else:
            logger.info(f"Status: InProgress")
        time.sleep(5)


if __name__ == '__main__':
    INSTANCE_ID, REGION = _configure()
    main(INSTANCE_ID, REGION)
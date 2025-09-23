#!/usr/bin/python

# The below shell script can be used to extract the instance ids from the import.sh/import.py file
# From import.sh - grep -oE 'i-[^. ]*' import.sh | sort -u | tr '\n' ',' | sed '$s/.$//' && echo
# From import.py - grep -oE 'i-[^. ]*' import.py | sed 's/..$//' | sort -u | tr '\n' ',' | sed '$s/.$//' && echo

# Syntax for command-
# python ami-creation.py -i i-12345678,i-87654321,i-xxxxxxxxxx,etc

import boto3
import sys
import argparse

session = boto3.session.Session()

def _configure():
    parser = argparse.ArgumentParser(description=['Insert the ID of the Target Instance'])
    parser.add_argument('-i','--instance-id', help='Target Instance ID', nargs='?', dest="instanceid")
    args = vars(parser.parse_args())

    instance_ids = [str(item) for item in args["instanceid"].split(',')]

    return instance_ids

def main(instanceIds):
    instances = get_instances(instanceIds)
    stop_instances(instances)
    create_ami(instances)
    start_instances(instances)

def get_instances(instanceIds):
    ec2_client = boto3.client("ec2")
    ec2 = boto3.resource("ec2", region_name=session.region_name)
    instances = ec2.instances.filter(
        InstanceIds=instanceIds
    )

    return instances

def stop_instances(instances):
    for instance in instances:
        for tag in instance.tags:
            if tag["Key"] == "Name":
                print('Stopping instance "{}"'.format(tag["Value"]))
                instance.stop()
    print(waiter(instances, "stop"))

def create_ami(instances):
    ssm = boto3.client('ssm', region_name='eu-west-2')
    try:
        customerName = ssm.get_parameter(Name='/aft/account-request/custom-fields/customer')
    except ssm.exceptions.ParameterNotFound:
        print("/aft/account-request/custom-fields/customer - does not exist\nRebooting instances and exiting script")
        start_instances(instances)
        sys.exit(1)
    for instance in instances:
        for tag in instance.tags:
            if tag["Key"] == "Name":
                image = instance.create_image(
                    Name=tag["Value"] + "-AMI",
                    Description="AMI created after migration",
                    NoReboot=True,
                    TagSpecifications=[
                        {
                            "ResourceType": "image",
                            "Tags": [
                                {
                                    "Key": "map-migrated",
                                    "Value": "sap49261",
                                },
                                {
                                    "Key": "CustomerName",
                                    "Value": customerName['Parameter']['Value'],
                                }
                            ],
                        },
                    ],
                )

        print(f"AMI creation started: {image.id}")
        image.wait_until_exists(Filters=[{"Name": "state", "Values": ["pending"]}])
    verify_ami(instances)

def verify_ami(instances):
    ec2_client = boto3.client("ec2")
    
    waiter = ec2_client.get_waiter('image_available')

    for instance in instances:
        for tag in instance.tags:
            if tag["Key"] == "Name":
                image = waiter.wait(
                    Filters=[
                        {
                            'Name': 'name',
                            'Values': [
                                tag["Value"] + "-AMI",
                            ]
                        },
                    ],
                    WaiterConfig={
                        'Delay': 10,
                        'MaxAttempts': 180
                    }
                )
                print(f"AMI " + tag["Value"] + "-AMI" + " successfully created")

def waiter(instances, state):
    ec2_client = boto3.client("ec2")
    if state == "start":
        waiter = ec2_client.get_waiter('instance_running')
        msg = "Instances started"
    else:
        waiter = ec2_client.get_waiter('instance_stopped')
        msg = "Instances stopped"
    
    for instance in instances:
        waiter.wait(
            InstanceIds=[
                instance.id,
            ],
            WaiterConfig={
                'Delay': 15,
                'MaxAttempts': 80
            }
        )
    return msg

def start_instances(instances):
    for instance in instances:
        for tag in instance.tags:
            if tag["Key"] == "Name":
                print('Starting instance "{}"'.format(tag["Value"]))
                instance.start()
    print(waiter(instances, "start"))

if __name__ == "__main__":
    INSTANCE_ID = _configure()
    main(INSTANCE_ID)

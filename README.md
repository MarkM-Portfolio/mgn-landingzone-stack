# Script collection to help working with AWS Application Migration Service
This collection of scripts and templates are meant to make working with MGN more easy. It consists of utility scripts to be executed on local machines, but also scripts meant to be part of an event-driven architecture to automate certain tasks to be done on each Lift & Shift migration  

## Utility scripts
All scripts require an engineer to `awsume` into the target account first and to provide valid credentials.   

* **mgn_listing.py**  
Script to get an at glance overview of servers replicated via MGN. It presents details of each server that one only can get when clicking on individual servers on the MGN console.
This script can be used to validate that individual launch configuration are set as expected.  

* **cutover_launch_template_change.py**  
This script parses MGN for all servers in state _READY_FOR_CUTOVER_ and changes the launch template to set the AWS Security Groups as required when moving to production  

* **populate_infra_manifest.py**  
Script that parses the Infrastructure Manifest sheet of a runbook and populates relevant configs to AWS SSM Parameter Store. Other scripts and templates relay on the information put to 
parameter store by this script. It is supposed to be run as soon as an AWS account for a customer workload is created and the runbook was signed off by the customer  

## Lambda functions
* **update_launch_template.py**  
This Lambda function is supposed to be triggered once a source server in MGN completes the initial sync and becomes READY_FOR_TEST for the first time. This lambda function looks up
configuration values in parameter store that were populated by an engineer with the **populate_infra_manifest.py** script. If configuration could be found in parameter store the function
will create a new EC2 Launch Template version to spin up EC2 instances with the correct settings as per the _Infrastructure Manifest_ of the corresponding runbook  

## Tools used for development
* [pipenv](https://pipenv.pypa.io/en/latest/) for managing python package dependencies and virtual python environment
* [asdf](https://asdf-vm.com/guide/introduction.html#how-it-works) for tool version management 
* [PyCharm](https://www.jetbrains.com/pycharm/)
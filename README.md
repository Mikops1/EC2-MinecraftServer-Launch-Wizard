# EC2-MinecraftServer-Launch-Wizard
Simple GUI to start/stop an EC2 instance and then start/stop a Minecraft server on it

Before using please ensure the following:

You have setup correct credentials in Amazon CLI on the device you're using and you have CLI access with the keypair file
Desired server files are already on the EC2 Instance
The linked JSON file has the correct data:
    "aws_region" - region where instance is setup
    "key_path" - path to keypair
    "instance_id" - id of instance to be used
    "instance_ids" - same as above
    "server_path" - path to server slh file on EC2 Instance

EC2 Permissions needed are:
    RunInstances
    StartInstances
    StopInstances
    DescribeInstanceAttribute
    DescribeInstances
    DescribeInstanceStatus
    DescribeInstanceTypes
    

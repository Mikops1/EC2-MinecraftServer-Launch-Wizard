import time
import json
from tkinter import *
import paramiko
import tkinter as tk
from mcstatus import JavaServer
import boto3
import threading
import os
import tkinter.messagebox as messagebox
# Get the directory path of Main.py
dir_path = os.path.dirname(os.path.realpath(__file__))
def check_keypair_file():
    # Check if the keypair file exists in the directory
    keypair_file = os.path.join(dir_path, 'Keypair1.pem')
    if os.path.isfile(keypair_file):
        # Update the key_path variable in variables.json
        with open('variables.json', 'r') as f:
            variables = json.load(f)
        variables['key_path'] = keypair_file
        with open('variables.json', 'w') as f:
            json.dump(variables, f)



#Import variables from json file
check_keypair_file()

VARIABLES_FILE = os.path.join(os.path.dirname(__file__), 'variables.json')
f = open(VARIABLES_FILE)
variables = json.load(f)


AWS_REGION = variables['aws_region']
KeyPath = variables['key_path']
INSTANCE_ID = variables['instance_id']
INSTANCE_IDS = variables['instance_ids']
SERVER_PATH = variables['server_path']

#Define boto3 clients
EC2_RESOURCE = boto3.resource('ec2', region_name=AWS_REGION)
ec2 = boto3.client('ec2', region_name=AWS_REGION)
ssm = boto3.client('ssm')
sts_client = boto3.client('sts')
response = sts_client.get_caller_identity()
username = response['Arn'].split('/')[1]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#Define functions
#Get instance status
def ReceiveStatus ():
    EC2_RESOURCE = boto3.resource('ec2', region_name=AWS_REGION)
    instance = EC2_RESOURCE.Instance(INSTANCE_ID)# type: ignore
    comp = {instance.state["Name"]}
    print (comp)
    return str(comp)

#Turn on instance
def TurnOn():
    if "run" in str(ReceiveStatus()):
        return
    ec2.start_instances(InstanceIds = INSTANCE_IDS, AdditionalInfo='string', DryRun = False) # type: ignore
    time.sleep(5)
    UpdateStatus()

#Turn off instance
def TurnOff():
    if "stop" in str(ReceiveStatus()):
        return
    EC2_RESOURCE.Instance(INSTANCE_ID).stop() # type: ignore
    time.sleep(5)
    UpdateStatus()
   
#Get public IP of instance
def get_public_ip(instance_id):
    reservations = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"]
    for reservation in reservations:
        for instance in reservation["Instances"]:
            return(instance.get("PublicIpAddress"))

#Get public DNS of instance
def get_public_dns(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    public_dns = response['Reservations'][0]['Instances'][0]['PublicDnsName']
    return public_dns

#Update status
def UpdateStatus():
    init = ReceiveStatus()
    fin = init
    count =20
    statusmsg.set(fin)
    loadmsg.set("Loading")
    load = 0
    root.update()
    while (count != 0 and fin == init):
        load = load + 5
        msg = "Loading (" + str(load) + " )"
        loadmsg.set(msg)
        root.update()
        fin = ReceiveStatus()
        time.sleep(5)
        count = count-1
    if "run" in str(ReceiveStatus()):
        loadmsg.set("IP: " + str(get_public_ip(INSTANCE_ID)))
    else:
        loadmsg.set("")
    statusmsg.set(fin)
    root.update()

def test_server():
    run_commands_ssh(["cd /home/ec2-user/Servers","mkdir test"])


#Run commands on instance   
def run_commands_ssh(commands):
    address = str(get_public_dns(INSTANCE_ID))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=address, username='ec2-user', key_filename=KeyPath)

    command = ' && '.join(commands)
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    ssh.close()

    return output, error



#Start Minecraft server
def start_mc_server():
    command = ["screen -dmS McServer bash -c 'cd " + SERVER_PATH + " && ./run.sh'"]
    mcserverstatus.set("Starting Minecraft Server...")
    root.update()
    run_commands_ssh(command)
    time.sleep(30)
    refresh()
 
#Stop Minecraft server   
def stop_mc_server():
    mcserverstatus.set("Closing Minecraft Server...")
    root.update()
    run_commands_ssh(["screen -S McServer -X stuff 'stop^M'", "sleep 15", "screen -S McServer -X quit"])
    refresh()

#Refresh status
def refresh():
    check_mc_server()
    statusmsg.set(str(ReceiveStatus()))
    root.update()

#Check if players are online
def check_players():
    if "run" in str(ReceiveStatus()):   
        while True:
            # Check if Minecraft server is running
            server = JavaServer.lookup(str(get_public_ip(INSTANCE_ID)) + ':25565')
            try:
                status = server.status()
                if status.players.online == 0:
                    mcserverstatus.set("No players online, counting down...")
                    start_countdown()
                mcserverstatus.set("Minecraft Server Online")
            except:
                mcserverstatus.set("Minecraft Server Offline")
                root.update()
                pass

            # Wait for 5 minutes
            time.sleep(300)
    else:
        mcserverstatus.set("Minecraft Server Offline")
        root.update()
        time.sleep(300)
        check_players()
#Check if minecraft server is running
def check_mc_server():
    # Check if Minecraft server is running
    server = JavaServer.lookup(str(get_public_ip(INSTANCE_ID)) + ':25565')
    try:
        status = server.status()
        if status.players.online == 0:
            mcserverstatus.set("No players online, counting down...")
        else:
            mcserverstatus.set("Minecraft Server Online")
    except:
        mcserverstatus.set("Minecraft Server Offline")
        root.update()
#Start countdown to shutdown
def start_countdown():
    for i in range(5, 0, -1):
        mcserverstatus.set("No players online, shutting down in " + str(i) + " minutes...")
        root.update()
        time.sleep(60)

        # Check if Minecraft server is running
        server = JavaServer.lookup(str(get_public_ip(INSTANCE_ID)) + ':25565')
        try:
            status = server.status()
            if status.players.online > 0:
                return
        except:
            pass

    # Stop the instance
    loadmsg.set("Shutting down instance...")
    root.update()
    stop_mc_server()
    TurnOff()
 

   
#Create GUI
root = tk.Tk()

# Set the window title
root.title("My Minecraft Server")

refreshicon = PhotoImage(file= dir_path +r"\refresh-icon.png")
refreshicon = refreshicon.subsample(18, 18)

cogicon = PhotoImage(file= dir_path + r"\cog-icon.png")
cogicon = cogicon.subsample(2, 2)

root.geometry('400x300')
loadmsg = tk.StringVar(root)
loadmsg.set("")

statusmsg = tk.StringVar(root)
statusmsg.set(str(ReceiveStatus()))

label1 = Label(root, text="Instance Status:", font=("Arial", 14)).place(x=70, y=20)
label2 = Label(root, textvariable=statusmsg, font=("Arial", 14)).place(x=210, y=20)
labelwait = Label(root, textvariable=loadmsg, font=("Arial", 10)).place(x=120,y=50)

mcserverstatus = tk.StringVar(root)
mcserverstatus.set("")
def open_config_window():
    # Create the configuration window
    config_window = tk.Toplevel(root)
    config_window.title("Configuration")
    config_window.geometry("400x350")

    # Load variables from JSON file
    f = open(VARIABLES_FILE)
    variables = json.load(f)

    # Create the input fields
    aws_region_label = tk.Label(config_window, text="AWS Region:")
    aws_region_label.pack()
    aws_region_entry = tk.Entry(config_window, width = 40)
    aws_region_entry.insert(0, variables['aws_region'])
    aws_region_entry.pack()

    key_path_label = tk.Label(config_window, text="Key Path:")
    key_path_label.pack()
    key_path_entry = tk.Entry(config_window, width = 40)
    key_path_entry.insert(0, variables['key_path'])
    key_path_entry.pack()

    instance_id_label = tk.Label(config_window, text="Instance ID:")
    instance_id_label.pack()
    instance_id_entry = tk.Entry(config_window, width = 40)
    instance_id_entry.insert(0, variables['instance_id'])
    instance_id_entry.pack()

    server_path_label = tk.Label(config_window, text="Server Path:")
    server_path_label.pack()
    server_path_entry = tk.Entry(config_window, width = 40)
    server_path_entry.insert(0, variables['server_path'])
    server_path_entry.pack()

    # Save the changes to the JSON file
    def save_changes():
        if aws_region_entry.get() and key_path_entry.get() and instance_id_entry.get() and server_path_entry.get():
            variables['aws_region'] = aws_region_entry.get()
            variables['key_path'] = key_path_entry.get()
            variables['instance_id'] = instance_id_entry.get()
            variables['server_path'] = server_path_entry.get()

            with open(VARIABLES_FILE, 'w') as f:
                json.dump(variables, f)

            config_window.destroy()
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    # Create the save button
    save_button = tk.Button(config_window, text="Save", command=save_changes)
    save_button.pack()
if "run" in str(ReceiveStatus()):
    loadmsg.set("IP: " + str(get_public_ip(INSTANCE_ID)))

btncog = Button(root, image=cogicon, bd='3', command= open_config_window)
btncog.place(x=330, y=10)

btnref = Button(root, image=refreshicon, bd = '3', command = refresh).place(x=10, y=10)
btnOn = Button(root, text = "Turn on", bd = '5',
    command = TurnOn ).place(x=60, y=100)
btnOff = Button(root, text = "Turn off", bd = '5',
    command = TurnOff).place(x=250, y=100)

btnStart = Button(root, text = "Start Server", bd = '5',
    command = start_mc_server).place(x=60, y=150)

btnStop = Button(root, text = "Stop Server", bd = '5',
    command = stop_mc_server).place(x=250, y=150)

labelmcserverrunning = Label(root, textvariable=mcserverstatus, font=("Arial", 12)).place(x=50, y=220)
player_thread = threading.Thread(target=check_players)
player_thread.start()

# Add label to display currently used credentials
credentials_label = Label(root, text="Currently used credentials: " + str(username), font=("Arial", 10)).place(x=10, y=270)
def on_closing():
    if "run" in str(ReceiveStatus()):
        if messagebox.askyesno("Close", "Do you want to close the server and instance?"):
            stop_mc_server()
            TurnOff()
            root.destroy()
            
        else:
            root.destroy()
            
    else:
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

    threading.Event().set()
    root.quit()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()


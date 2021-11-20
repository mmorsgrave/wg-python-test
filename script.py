#!/usr/bin/python3
from os import strerror, write
import paramiko
import time
import json

new_values = {"brunch": "", "revision" : ""}
current_brunch = ""
current_revision = ""
json_file = None
error_branch_message = ""
error_revision_message = ""

def get_clear_str(list):
    str = "".join(list)
    return str.rstrip()

def get_git_branch(str):
    git_branch = str.split("/")
    return git_branch[len(git_branch)-1]

def get_svn_branch(str):
    return str.replace("Relative URL: ", "")

def get_svn_revision(str):
    return str.replace("Revision: ", "")

with open("JSON") as file:
    json_file = json.load(file)

for cluster in json_file['hosts']:
    for item, value in json_file['hosts'][cluster].items():
        if item == "host":
            current_host = value
        if item == "user":
            current_user = value
    print ("current host is: " + current_host)
    print ("current user is: " + current_user)

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(current_host,username=current_user, password=current_user)
    except:
        print(f"unable to connect to {current_host}")
        ssh.close()
        continue

    # git
    stdin, stdout, stderr = ssh.exec_command("cat ~/bw/wg-test/.git/HEAD")
    time.sleep(0.1)    
    current_brunch = get_git_branch (get_clear_str(stdout.readlines()))
    error_branch_message = get_clear_str(stderr.readlines())

    stdin, stdout, stderr = ssh.exec_command("cd ~/bw && git rev-parse HEAD")
    time.sleep(0.1)
    current_revision = get_clear_str(stdout.readlines())
    error_revision_message = get_clear_str(stderr.readlines())
   
    # В случае отстутствия гита или неверной директории вывод попадет в stderr, stdout будет пустой
    if current_brunch == "":
        print("git branch error: " + error_branch_message)
        print("git revision error: " + error_revision_message)
    
        # svn
        stdin, stdout, stderr = ssh.exec_command("cd ~/bw && svn info | grep \"Relative URL\"")
        time.sleep(0.1)    
        current_brunch = get_svn_branch(get_clear_str(stdout.readlines())) 
        error_branch_message = get_clear_str(stderr.readlines())

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/svn/project/project && svn info | grep \"Revision\"")
        time.sleep(0.1)        
        current_revision = get_svn_revision(get_clear_str(stdout.readlines()))
        error_revision_message = get_clear_str(stderr.readlines())

        # если отсутствует и svn в текущей директории или он не установлен в системе, запись новых значений в исходный json файл
        # не производим
        if current_brunch == "":
            print("svn branch error: " + error_branch_message)
            print("svn revision error: " + error_revision_message)
            ssh.close()
            continue

    print (f"current {current_host} brunch is: " + current_brunch)
    print (f"current {current_host} revision is: " + current_revision)
    
    new_values["brunch"] = current_brunch
    new_values["revision"] = current_revision

    json_file["hosts"][cluster].update(new_values)
    
    with open("JSON", "w") as new_file:
        temp = json.dumps(json_file)
        new_file.write(temp)
    ssh.close()

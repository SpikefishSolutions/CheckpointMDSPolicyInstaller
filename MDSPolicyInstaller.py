# import checkpoint api. See
# https://github.com/CheckPointSW/cp_mgmt_api_python_sdk
# the first time this script is run it will check the finger print
# of the api url and prompt yes/no to save a finger print to a file.

from cpapi import APIClient, APIClientArgs
import time
import json
import pprint
import csv
# output will be sent to this file 
# output file will be overwritten (not appended)
output='policy_install_status.txt'
csvfile = open(output, "w") 
# clobber output file.
csvfile.seek(0)
csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
# These are the headers for the csv file.
csvwriter.writerow(['Domain','Policy','Target','Gateway','Message','ErrLevel'])

api_server = 'SomeHost'
username   = 'SomeUsername'
password   = 'SomePassword'

# this is basically just used to help 
# format json output should you want to see it
pp = pprint.PrettyPrinter(indent=4)

def main():

    #client_args = APIClientArgs(server=api_server,http_debug_level=5)
    client_args = APIClientArgs(server=api_server)

    with APIClient(client_args) as client:
        login_res = client.login(username, password)

        if login_res.success is False:
            print("Login Failed:\n{}".format( login_res.error_message ))
            exit(1)
                
        domains = client.api_query("show-domains",container_key="objects")
        for domain in domains.data:

            domain_name = domain['name']

            with APIClient(client_args) as domain_client:
                login_res = client.login(username, password, domain=domain_name)

                if login_res.success is False:
                    print("Can't login to CMA: {}\n{}".format(domain, login_res.error_message))
                    exit(1)
         
                policy_packages = client.api_query("show-packages",container_key="packages")
                for policy_package in policy_packages.data:
                     policy_package_name = policy_package['name']
                     #print(policy_package_name)

                     json_data = {"name": policy_package_name} 
                     policy_package = client.api_call("show-package", payload=json_data)
                     policy_installation_targets =  policy_package.data["installation-targets"]
                     if isinstance(policy_installation_targets, str):
                         pass
                         #print("Skipping targets set to all Domain: {} Policy: {} install target: {}".format(
                         #    domain_name, policy_package_name, policy_installation_targets))
                     else:
                         for policy_installation_target in policy_installation_targets:
                             #print("Domain: {} Policy: {} install target: {}".format(
                             #    domain_name, policy_package_name, policy_installation_target['name']))
                             json_data = {"policy-package": policy_package_name,
                                          "targets":        policy_installation_target['name']} 
                             while True:
                                 policy_install_status = client.api_call("install-policy", payload=json_data)
                                 if policy_install_status.status_code == 409:
                                     print("Policy install in progress. Sleeping for 10 seconds.")
                                     time.sleep(10)
                                     next
                                 else:
                                     for tasks in policy_install_status.data['tasks']:
                                         taskdetails = tasks['task-details']
                                         #print("Task details")
                                         #pp.pprint(taskdetails)
                                         for taskdetail in taskdetails:
                                             gateway_name = taskdetail['gatewayName']
                                             #print("Task detail")
                                             #pp.pprint(taskdetail)
                                             #print(['Domain,Policy,Target,Gateway,Message,ErrLevel'])
                                             for stagesInfo in taskdetail['stagesInfo']:
                                                 for message in stagesInfo['messages']:
                                                     #print(domain_name, policy_package_name, policy_installation_target['name'],
                                                     #      gateway_name, message['message'], message['type'])
                                                     csvwriter.writerow([domain_name, policy_package_name, 
                                                               policy_installation_target['name'],
                                                               gateway_name, message['message'], message['type']])

                                     # break while True loop
                                     break   



if __name__ == "__main__":
    main()

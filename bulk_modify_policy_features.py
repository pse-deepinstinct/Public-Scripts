# Example of how to modify a policy setting or set of setting in bulk, including
# an unlimited quantity of policies on 1 or more managenent servers, in a single
# script. On a multi-tenancy server, the scope of policies modified will depend
# upon the privileges of the API key(s) you provide in the server_list.
#
# DEEP INSTINCT MAKES NO WARRANTIES OR REPRESENTATIONS REGARDING DEEP INSTINCT’S 
# PROGRAMMING SCRIPTS. TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, 
# DEEP INSTINCT DISCLAIMS ALL OTHER WARRANTIES, REPRESENTATIONS AND CONDITIONS, 
# WHETHER EXPRESS, STATUTORY, OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, ANY 
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE OR 
# NON-INFRINGEMENT, AND ANY WARRANTIES ARISING OUT OF COURSE OF DEALING OR USAGE 
# OF TRADE. DEEP INSTINCT’S PROGRAMMING SCRIPTS ARE PROVIDED ON AN "AS IS" BASIS, 
# WITHOUT WARRANTY OF ANY KIND, AND DEEP INSTINCT DISCLAIMS ALL OTHER WARRANTIES, 
# EXPRESS, IMPLIED OR STATUTORY, INCLUDING ANY IMPLIED WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.
#
#
server_list = [

{'fqdn': 'SERVER1.customers.deepinstinctweb.com',
'key': 'KEY1'},

{'fqdn': 'SERVER2.customers.deepinstinctweb.com',
'key': 'KEY2'},

{'fqdn': 'SERVER3.customers.deepinstinctweb.com',
'key': 'KEY3'},

]


#import required libraries
import requests
import json

for server in servers:

    #define DI server config
    fqdn = server['fqdn']
    key = server['key']

    #get list of policies
    request_url = f'https://{fqdn}/api/v1/policies/'
    headers = {'accept': 'application/json', 'Authorization': key}
    response = requests.get(request_url, headers=headers)
    policies = response.json()

    for policy in policies:
        #for every Windows policy
        if policy['os'] == 'WINDOWS':
            #get policy data from server
            request_url = f'https://{fqdn}/api/v1/policies/{policy["id"]}/data'
            response = requests.get(request_url, headers=headers)
            policy_data = response.json()
            #modify policy data
            if policy_data['data']['dual_use'] in ['DETECT', 'PREVENT']:
                print(f"Modifying dual_use setting from '{policy_data['data']['dual_use']}' to 'ALLOW' for MSP '{policy['msp_name']}' (ID {policy['msp_id']}) Policy '{policy['name']}' (ID {policy['id']})")
                policy_data['data']['dual_use'] = 'ALLOW'
                #save modified policy data to server
                response = requests.put(request_url, json=policy_data, headers=headers)

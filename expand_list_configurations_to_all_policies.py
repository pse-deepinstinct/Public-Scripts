# Example of how to synchronize configuration across an unlimited number of
# policies, in this scenario by finding any allow lists, deny lists, or
# exclusion entries applied to some but not all policies and applying them
# to the additional policies.
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

import deepinstinct3 as di

#import required Python library
import requests

#define server config
#Note: On MT server, use an API key with Full Access to exactly 1 MSP
di.fqdn = 'FOO.customers.deepinstinctweb.com'
di.key = 'BAR'

#define what type(s) of records you want to promote to "all windows policies"
allow_deny_and_exclusion_list_types = ['allow-list/hashes', 'allow-list/paths', 'allow-list/certificates', 'allow-list/scripts', 'deny-list/hashes', 'exclusion-list/folder_path', 'exclusion-list/process_path']

#get policy data from server, including ally/deny/exclusion lists
all_policies = di.get_policies(include_allow_deny_lists=True, keep_data_encapsulated=True)

#build list of just Windows policies, and another with the policy IDs of just Windows policies
windows_policies = []
windows_policy_ids = []
for policy in all_policies:
    if policy['os'] == 'WINDOWS':
        windows_policies.append(policy)
        windows_policy_ids.append(policy['id'])

#iterate through Windows policies
print('Beginning work to synchronize configuration across', len(windows_policies), 'Windows policies on', di.fqdn, 'for the following data types:', allow_deny_and_exclusion_list_types)
for policy in windows_policies:
    print('Beginning processing of data that currently exists in policy', policy['id'], policy['name'])

    #iterate through configured data types
    for list_type in allow_deny_and_exclusion_list_types:
        print('Looking at data of type', list_type, 'in policy', policy['id'], policy['name'])

        #check if any exist
        if len(policy['allow_deny_and_exclusion_lists'][list_type]['items']) > 0:
            #yes, 1 or more exist
            print('Found', len(policy['allow_deny_and_exclusion_lists'][list_type]['items']) , 'items')

        #avoid HTTP 400 error when copying entries with null (None) comment by checking for error conditions (either no comment or comment=None and replacing with empty string)
        items_for_payload = policy['allow_deny_and_exclusion_lists'][list_type]['items']
        for item in items_for_payload:
            #print('DEBUG: This is the item:\n', item)
            if 'comment' not in item.keys():
                #print('DEBUG: Found an item with no comment. Before:\n', item)
                item['comment'] = ''
                #print('DEBUG: After:\n', item)
            elif item['comment'] == None:
                #print('DEBUG: Found an item with a null (None) comment. Before:\n', item)
                item['comment'] = ''
                #print('DEBUG: After:\n', item)

        #calculate payload and headers for applying these items to the other policy(s)
        payload = {'items': items_for_payload}
        headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': di.key}

        #iterate through Windows policy ids
        for policy_id in windows_policy_ids:

            #check that policy_id is not for the same policy we're copying data from
            if policy_id != policy['id']:

                print('Adding these entries to policy', policy_id)
                #calculate URL
                request_url = f'https://{di.fqdn}/api/v1/policies/{policy_id}/{list_type}'
                #send data to server
                response = requests.post(request_url, headers=headers, json=payload)
                if response.status_code == 204:
                    print('Success')
                else:
                    print('ERROR: Unexpected response', response.status_code, 'on POST to', request_url, 'with payload', payload, 'and headers', headers)
            else:
                #no, none exist. Nothing to do here.
                print('No data of this type exists. Moving on.')
    print('Done processing of data that currently exists in policy', policy['id'], policy['name'])

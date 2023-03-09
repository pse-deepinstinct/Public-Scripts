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
# Part 1 of a pair of scripts showing an example of how to handle a break/fix
# scenario where some (or many) devices were prematurely moved to a more
# restrictive policy.

#import API Wrapper (Python bindings) and additional libraries
import deepinstinct3 as di
import pandas, datetime
from dateutil import parser

#define server config
di.key = 'BAR'
di.fqdn = 'FOO.customers.deepinstinctweb.com'

#get events from server
search_parameters = {}
search_parameters['type'] = ['STATIC_ANALYSIS']
search_parameters['action'] = ['PREVENTED']
search_parameters['last_action'] = ['QUARANTINE_SUCCESS']
events = di.get_events(search=search_parameters)

#using events, calculate list of unique hashes
hash_list = []
for event in events:
    if event['file_hash'] not in hash_list:
        hash_list.append(event['file_hash'])

#get policies
all_policies = di.get_policies()

#filter policy list
windows_policies = []
for policy in all_policies:
    if policy['os'] == 'WINDOWS':
        windows_policies.append(policy)

#iterate through Windows policies and add the allow lists to each
for policy in windows_policies:
    di.add_allow_list_hashes(hash_list, policy['id'])

#save hash list and event list for later usage
hash_list_df = pandas.DataFrame(hash_list)
events_df = pandas.DataFrame(events)
folder_name = di.create_export_folder()
file_name = 'premature_prevention_recovery.xlsx'

with pandas.ExcelWriter(f'{folder_name}/{file_name}') as writer:
    hash_list_df.to_excel(writer, sheet_name='hash_list', index=False)
    events_df.to_excel(writer, sheet_name='event_list', index=False)

print('Data written to', f'{folder_name}/{file_name}')

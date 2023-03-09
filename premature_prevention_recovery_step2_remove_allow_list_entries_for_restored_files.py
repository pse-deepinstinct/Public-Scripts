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
# Part 2 of a pair of scripts showing an example of how to handle a break/fix
# scenario where some (or many) devices were prematurely moved to a more
# restrictive policy.

#import API Wrapper (Python bindings) and additional libraries
import deepinstinct3 as di
import pandas, datetime
from dateutil import parser

#define server config
di.key = 'BAR'
di.fqdn = 'FOO.customers.deepinstinctweb.com'

#read hash list from Excel file on disk
file_name = 'premature_prevention_recovery.xlsx'
folder_name = di.create_export_folder()
hash_list_df = pandas.read_excel(f'{folder_name}/{file_name}', sheet_name='hash_list')
hash_list_df.columns=['hashes']
hash_list = hash_list_df['hashes'].values.tolist()

#get events from server
search_parameters = {}
search_parameters['type'] = ['STATIC_ANALYSIS']
search_parameters['action'] = ['PREVENTED']
search_parameters['last_action'] = ['QUARANTINE_SUCCESS']
events = di.get_events(search=search_parameters)

#calculate list of hashes for files still in quarantine
hash_list_still_in_quarantine = []
for event in events:
    if event['file_hash'] not in hash_list_still_in_quarantine:
        hash_list_still_in_quarantine.append(event['file_hash'])

#calculate hashes safe to remove from allow list
hashes_to_remove = []
for hash in hash_list:
    if hash not in hash_list_still_in_quarantine:
        hashes_to_remove.append(hash)

#get policies
all_policies = di.get_policies()

#filter policy list
windows_policies = []
for policy in all_policies:
    if policy['os'] == 'WINDOWS':
        windows_policies.append(policy)

#iterate through Windows policies and remove the allow lists from each
for policy in windows_policies:
    di.remove_allow_list_hashes(hashes_to_remove, policy['id'])

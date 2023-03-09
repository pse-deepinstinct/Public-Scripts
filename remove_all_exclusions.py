# Example of how to bulk remove erroneous/unwanted configuration, for example
# to reset a demo or lab environemnt. In this example, all exclusions are
# removed from all Windows policies.
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

#prompt for config
di.fqdn = input('Enter FQDN of DI Server, or press enter to accept the default [di-service.customers.deepinstinctweb.com]: ')
if di.fqdn == '':
    di.fqdn = 'di-service.customers.deepinstinctweb.com'
di.key = input('Enter API Key for DI Server: ')

#get policy list, then filter it to get a list of just Windows policies
all_policies = di.get_policies()
print(len(all_policies), 'total policies on server')
windows_policies = []
for policy in all_policies:
    if policy['os'] == 'WINDOWS':
        windows_policies.append(policy)
print(len(windows_policies), 'of those are Windows policies')

#remove all exclusions from all Windows policies
for policy in windows_policies:
    print('Removing exclusions from policy', policy['id'], policy['name'])
    di.remove_all_exclusions(policy['id'], exclusion_types=['folder_path', 'process_path'])

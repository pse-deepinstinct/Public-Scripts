# Example of how to take bulk action on events programatically, in this example
# using event search to find all Static Analysis events for MS Office files
# and then adding all unique hashes to the allow list for all Windows policies
# before closing (and optionally archiving) the events.
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

#define server config
di.fqdn = 'FOO.customers.deepinstinctweb.com'
di.key = 'BAR'

#get events from server
search_parameters = {}
search_parameters['type'] = ['STATIC_ANALYSIS']
search_parameters['file_type'] = ['OFFICE', 'PPT', 'XLS', 'DOC']
search_parameters['trigger'] = ['MALICIOUS_FILE']
search_parameters['action'] = ['DETECTED']
events = di.get_events(search=search_parameters)

#using events, calculate list of unique hashes
hash_list = []
for event in events:
    if event['file_hash'] not in hash_list:
        hash_list.append(event['file_hash'])

#get windows policies
windows_policies = di.get_policies(os_list=['WINDOWS'])

#iterate through Windows policies and add the allow lists to each
for policy in windows_policies:
    di.add_allow_list_hashes(hash_list, policy['id'])

#using events, calculate list of event ids
event_id_list = []
for event in events:
    event_id_list.append(event['id'])

#break event_id_list into a list of smaller lists
batch_size = 250
event_id_list_broken_into_batches = [event_id_list[i:i + batch_size] for i in range(0, len(event_id_list), batch_size)]

#iterate through the batches of event ids and close (and optionally archive) them
batch_number = 1
for batch in event_id_list_broken_into_batches:

    print('Processing batch', batch_number, 'of', len(event_id_list_broken_into_batches))

    #close the events
    print('  Closing', len(batch), 'events')
    di.close_events(batch)

    #Optionally uncomment the code below to archive the events (in addition to closing them)
    #
    #print('  Archiving', len(batch), 'events')
    #di.archive_events(batch)

    batch_number += 1

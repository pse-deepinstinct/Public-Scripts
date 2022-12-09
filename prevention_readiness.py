# prevention_readiness.py
# Author: Patrick Van Zandt, Principal Professional Services Engineer
# November 2021

# This script provides an example of how to use the Deep Instinct REST API
# Wrapper published at https://github.com/pvz01/deepinstinct_rest_api_wrapper
# to programatically analyze deployment and event data and use a data-driven
# approach to identify devices currently in detection mode that are ready
# to move to prevention mode and to optionally move them to prevention groups.
# Source data showing the analysis is written to disk in Excel format.

# This script is provided as-is and with no warranty. Use at your own risk.

# Prerequisites:
# 1. Python 3.8 or later
# 2. Deep Instinct REST API Wrapper
# 3. Third-party libraries (strongly recommend to install Anaconda)
# 4. Network access to management server
# 5. API key with appropriate permissions (Read Only for analysis only | Full
#    Access if you chose to move devices when running script)

# Usage:
# 1. Save latest version of deepinstinct30.py from
#    https://github.com/pvz01/deepinstinct_rest_api_wrapper to disk
# 2. Save prevention_readiness.py to the same folder on disk
# 3. Optionally implement event filters by modifying the code below which
#    organizes events into included_events | excluded_events
# 4. Optionally modify the criteria for determining prevention readiness:
#    config['min_days_since_deployment'],config['max_days_since_last_contact'],config['max_weekly_event_rate']
# 5. Save modified script (if any changes were made)
# 6. Open a Command Prompt window, CD to the directory containing the 2 PY
#    files, and run this command: python prevention_readiness.py
# 7. When prompted, provide server FQDN in this format:
#    foo.customers.deepinstinctweb.com
# 8. When prompted, provide the API key and other configuration details, then
#    answer the prompts. You can exit any time with Ctrl+C.

# import required libraries
import deepinstinct30 as di, json, datetime, pandas
from dateutil import parser

#prompt for config
di.fqdn = input('Enter FQDN of DI Server, or press enter to accept the default [di-service.customers.deepinstinctweb.com]: ')
if di.fqdn == '':
    di.fqdn = 'di-service.customers.deepinstinctweb.com'

di.key = input('Enter API Key for DI Server: ')

config = {}

config['min_days_since_deployment'] = input('Enter minimum days since deployment, or press enter to accept the default [10]: ')
if config['min_days_since_deployment'] == '':
    config['min_days_since_deployment'] = 10

config['max_days_since_last_contact'] = input('Enter max days since last contact, or press enter to accept the default [3]: ')
if config['max_days_since_last_contact'] == '':
    config['max_days_since_last_contact'] = 3

config['max_weekly_event_rate'] = input('Enter max weekly event rate, or press enter to accept the default [2]: ')
if config['max_weekly_event_rate'] == '':
    config['max_weekly_event_rate'] = 2

user_response = input('Include closed events? Enter YES or NO, or press enter to accept the default [NO]: ')
if user_response.lower() == 'yes':
    config['include_closed_events'] = True
else:
    config['include_closed_events'] = False

user_response = input('Include Ransomware Behavior events? Enter YES or NO, or press enter to accept the default [YES]: ')
if user_response.lower() == 'no':
    config['include_ransomware_behavior_events'] = False
else:
    config['include_ransomware_behavior_events'] = True

user_response = input('Include In-Memory Protection Events? Enter YES or NO, or press enter to accept the default [YES]: ')
if user_response.lower() == 'no':
    config['include_in_memory_protection_events'] = False
else:
    config['include_in_memory_protection_events'] = True

config['minimum_event_id'] = input('Enter minimum_event_id as an integer, or press enter to accept the default [0]: ')
if config['minimum_event_id'] == '':
    config['minimum_event_id'] = 0

#get the data from DI server
print('INFO: Gathering data')
print('\tCalling get_devices')
devices = di.get_devices(include_deactivated=False)
print('\tCalling get_policies')
policies = di.get_policies(include_policy_data=True)
print('\tCalling get_groups')
groups = di.get_groups(exclude_default_groups=False)
print('\tCalling get_events (this may take a while)')
all_events = di.get_events(minimum_event_id=config['minimum_event_id'])
print('\t', len(all_events), 'events were returned.')
print('INFO: Filtering events')

#define two lists to organize events into
included_events = []
excluded_events = []

for event in all_events:

    if event['status'] == 'OPEN' or config['include_closed_events']:

        if event['type'] in ['STATIC_ANALYSIS']:
            if event['threat_severity'] in ['MODERATE', 'HIGH', 'VERY_HIGH']:
                included_events.append(event)

            # TODO: You can add more filters here for patterns of activity you have
            # either confirmed as a True Positive -or- you have confirmed as a
            # False Positive and added the appropriate allow list. Some examples
            # are below (commented out). You need to remove/comment out the above
            # code block and replace it wabuild *nested* if statements with a single
            # 'append' statement at the end

            #if event['type'] in ['STATIC_ANALYSIS']:
                #if event['threat_severity'] in ['MODERATE', 'HIGH', 'VERY_HIGH']:
                    #if event['file_hash'] not in ['alpha', 'bravo']:
                        #if event['path'][0:10] not in ['c:\\echo\\foxtrot\\']:
                            #if event['path'][0:28] not in ['/Users/paulinejolly/Library/']:
                                #if event['path'][0:22] not in ['/Users/workspace/berk/']:
                                    #included_events.append(event)

        #TODO: You might also consider removing some/many event types below, which
        #means they will always be excluded from analysis. This is useful if, for
        #example, you are evaluating Prevention Readiness only for specific DI
        #policy feature(s).
        #Alternately, you might create additional code based on the example
        #above (for Static Analysis) which excludes Behavioral events which you
        #have confirmed to be False Positives (and handled via Allow List) or True
        #Positives.

        elif event['type'] in ['RANSOMWARE_FILE_ENCRYPTION']:
            if config['include_ransomware_behavior_events']:
                included_events.append(event)

        elif event['type'] in ['REMOTE_CODE_INJECTION_EXECUTION', 'KNOWN_SHELLCODE_PAYLOADS', 'ARBITRARY_SHELLCODE', 'REFLECTIVE_DLL', 'REFLECTIVE_DOTNET', 'AMSI_BYPASS', 'DIRECT_SYSTEMCALLS', 'CREDENTIAL_DUMP']:
            if config['include_in_memory_protection_events']:
                included_events.append(event)

        elif event['type'] in ['MALICIOUS_POWERSHELL_COMMAND_EXECUTION']:
                included_events.append(event)

        else:
            excluded_events.append(event)

    else:
        excluded_events.append(event)


print('     ', len(excluded_events), 'were excluded from analysis and', len(included_events), 'events remain')

#count the filtered events by device_id
print('INFO: Summarizing included events by device_id')
event_counts = di.count_data_by_field(included_events, 'device_id')

print('INFO: Adding prevention_mode field to policy data')
prevention_policy_count = 0
detection_policy_count = 0
for policy in policies:
    policy['prevention_mode'] = di.is_prevention_policy(policy)
    if policy['prevention_mode']:
        prevention_policy_count += 1
        if di.debug_mode:
            print('INFO:', policy['os'], policy['id'], policy['name'], 'is a prevention mode policy')
    else:
        detection_policy_count += 1
        if di.debug_mode:
            print('INFO:', policy['os'], policy['id'], policy['name'], 'is not a prevention mode policy (detection or hybrid)')
print('      Found', prevention_policy_count, 'prevention policies and', detection_policy_count, 'detection/hybrid policies')


#add in_prevention field to devices
print('INFO: Adding prevention_mode field to device data')
for device in devices:
    for policy in policies:
        if policy['id'] == device['policy_id']:
            device['in_prevention'] = policy['prevention_mode']

#add event_count field to devices
print('INFO: Adding event_count field to device data')
for device in devices:
    if device['id'] in event_counts.keys():
        device['event_count'] = event_counts[device['id']]
    else:
        device['event_count'] = 0

#add associated policy name and prevention mode to group data (for display purposes only)
print('INFO: Adding policy_name and prevention_mode to device group data')
for group in groups:
    for policy in policies:
        if group['policy_id'] == policy['id']:
            group['policy_name'] = policy['name']
            group['prevention_mode'] = policy['prevention_mode']

#add days_since_deployment field to devices
print('INFO: Adding days_since_deployment to device data by comparing last_registration to current datetime')
for device in devices:
    device['days_since_deployment'] = (datetime.datetime.now(datetime.timezone.utc) - parser.parse(device['last_registration'])).days

#add days_since_last_contact field to devices
print('INFO: Adding last_contact_days_ago to device data by comparing last_contact to current datetime')
for device in devices:
    device['last_contact_days_ago'] = (datetime.datetime.now(datetime.timezone.utc) - parser.parse(device['last_contact'])).days

#add weekly_event_rate field to devices
print('INFO: Adding weekly_event_rate to device data')
for device in devices:
    if device['days_since_deployment'] > 0:
        device['weekly_event_rate'] = device['event_count'] / device['days_since_deployment'] * 7
    else:
        device['weekly_event_rate'] = device['event_count'] * 7

#add ready_for_prevention field to devices
print('INFO: Evaluating devices to determine prevention readiness and recoding it in device data as ready_for_prevention')
for device in devices:
    device['ready_for_prevention'] = False
    if device['days_since_deployment'] >= int(config['min_days_since_deployment']):
        if device['last_contact_days_ago'] <= int(config['max_days_since_last_contact']):
            if device['weekly_event_rate'] <= int(config['max_weekly_event_rate']):
                device['ready_for_prevention'] = True

#sort devices into 3 lists by category
print('INFO: Sorting devices into category-specific lists (already_in_prevention | ready_for_prevention | not_ready_for_prevention)')
devices_already_in_prevention = []
devices_ready_for_prevention = []
devices_not_ready_for_prevention = []
for device in devices:
    if device['in_prevention']:
        devices_already_in_prevention.append(device)
    elif device['ready_for_prevention']:
        devices_ready_for_prevention.append(device)
    else:
        devices_not_ready_for_prevention.append(device)

print('INFO: Calculating how many devices in each group are ready for prevention')
for group in groups:
    group['devices_ready_for_prevention'] = 0
for device in devices_ready_for_prevention:
    for group in groups:
        if device['group_id'] == group['id']:
            group['devices_ready_for_prevention'] +=1

print('INFO: Building list of groups with devices ready for prevention')
groups_with_devices_ready_for_prevention = []
for group in groups:
    if group['devices_ready_for_prevention'] > 0:
        groups_with_devices_ready_for_prevention.append(group)
print('INFO: Done with calculations')

#export data to disk
folder_name = di.create_export_folder()
file_name = f'prevention_readiness_assessment_{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H.%M")}_UTC.xlsx'
print('INFO: Exporting results including source data to disk as', f'{folder_name}/{file_name}')
event_counts_df = pandas.DataFrame((event_counts.items()))
devices_df = pandas.DataFrame(devices)
policies_df = pandas.DataFrame(policies)
groups_df = pandas.DataFrame(groups)
devices_already_in_prevention_df = pandas.DataFrame(devices_already_in_prevention)
devices_ready_for_prevention_df = pandas.DataFrame(devices_ready_for_prevention)
devices_not_ready_for_prevention_df = pandas.DataFrame(devices_not_ready_for_prevention)
all_events_df = pandas.DataFrame(all_events)
included_events_df = pandas.DataFrame(included_events)
excluded_events_df = pandas.DataFrame(excluded_events)
with pandas.ExcelWriter(f'{folder_name}/{file_name}') as writer:
    devices_ready_for_prevention_df.to_excel(writer, sheet_name='ready_for_prevention', index=False)
    devices_not_ready_for_prevention_df.to_excel(writer, sheet_name='not_ready_for_prevention', index=False)
    devices_already_in_prevention_df.to_excel(writer, sheet_name='already_in_prevention', index=False)
    devices_df .to_excel(writer, sheet_name='all', index=False)
    event_counts_df.to_excel(writer, sheet_name='event_counts', index=False)
    policies_df.to_excel(writer, sheet_name='policies', index=False)
    groups_df.to_excel(writer, sheet_name='groups', index=False)
    all_events_df.to_excel(writer, sheet_name='all_events', index=False)
    included_events_df.to_excel(writer, sheet_name='included_events', index=False)
    excluded_events_df.to_excel(writer, sheet_name='excluded_events', index=False)

#print summary data
print()
print('-----')
print('SUMMARY OF FINDINGS:')
print('-----')
print(len(devices), 'total devices with an activated license on', di.fqdn)
print(len(devices_already_in_prevention), 'of those are already in prevention')
print(len(devices_not_ready_for_prevention), 'are not yet ready to move to prevention based on the criteria provided')
print(len(devices_ready_for_prevention), 'are ready to move to prevention')
print()
print('-----')
print('CRITERIA USED IN ABOVE CALCULATIONS:')
print('-----')
print(json.dumps(config, indent=4))
print()
print('The', len(devices_ready_for_prevention), 'devices ready to move to prevention are currently in the following', len(groups_with_devices_ready_for_prevention), 'Device Group(s):')
print(json.dumps(groups_with_devices_ready_for_prevention, indent=4))
print()

execute_moves_now = ''

if len(devices_ready_for_prevention) == 0:
    execute_moves_now = False
else:
    execute_moves_now = ''

while execute_moves_now not in (True, False):
    response = input('Do you want to choose groups and move some or all devices to prevention mode now [YES | NO]? ')
    if response.lower() == 'yes':
        execute_moves_now = True
    elif response.lower() == 'no':
        execute_moves_now = False

if execute_moves_now:
    #for each group with 1 or more devices ready for prevention, calculate valid new groups and prompt user to select one
    for old_group in groups_with_devices_ready_for_prevention:
        print('INFO: Calcuating possible destination groups for devices currently in Device Group', old_group['id'], old_group['name'])
        destination_group_options = []
        for group in groups:
            if group['msp_id'] == old_group['msp_id']:
                if group['os'] == old_group['os']:
                    if not group['is_default_group']:
                        if group['id'] != old_group['id']:
                            if group['prevention_mode']:
                                destination_group_options.append(group)
        print('')
        print('The', old_group['devices_ready_for_prevention'], 'devices in',
                old_group['os'], old_group['id'], old_group['name'],
                'can be moved to one of the following groups:')
        print(json.dumps(destination_group_options, indent=4))
        print()
        old_group['destination_group_id'] = input('What is the ID of the group you want to move them to? ')

    print()
    print('INFO: Done collecting data and selecting destination groups')

print()

if execute_moves_now:
    print('INFO: Beginning to move devices')
    for group in groups_with_devices_ready_for_prevention:

        source_group_id = group['id']
        destination_group_id = group['destination_group_id']

        device_ids_to_move = []
        for device in devices_ready_for_prevention:
            if device['group_id'] == source_group_id:
                device_ids_to_move.append(device['id'])

        print('INFO: Moving', len(device_ids_to_move), 'devices from group', source_group_id, 'to group', destination_group_id)

        user_input = input('Do you want to proceed? If yes, type YES and press return: ')
        if user_input.lower() == 'yes':
            if not di.add_devices_to_group(device_ids_to_move, destination_group_id):
                print('ERROR: The move of devices from group', source_group_id, 'to group', destination_group_id, 'failed.')
        else:
            print('WARNING: Skipping move of devices currently in group', source_group_id, 'based on response above:', user_input)

    print('INFO: Done with device moves')

print('INFO: Script is complete')

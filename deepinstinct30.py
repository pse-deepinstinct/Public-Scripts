# Deep Instinct v3.0 REST API Wrapper
# Patrick Van Zandt, Principal Professional Services Engineer, Deep Instinct
#
# Compatibility:
# -Deep Instinct D-Appliance versions 3.0.x, 3.1.x, and 3.2.x
# -Written and tested using a Python 3.8.3 instance installed by Anaconda
#
# Suggested Usage:
# 1. Save this file as deepinstinct30.py in the same directory as your code
# 2. Include "import deepinstinct30 as di" at the top of your code
# 3. Set/modify the DI server name like this: di.fqdn = 'SERVER-NAME'
# 4. Set/modify the DI REST API key like this: di.key = 'API-KEY'
# 5. Invoke the REST API methods like this:  di.function_name(arg1, arg2)
# 6. For testing and interactive usage, I use and recommend Jupyter Notebook,
#    which is installed as part of Anaconda (https://www.anaconda.com/)
#
# Disclaimer:
# This code is provided as an example of how to build code against and interact
# with the Deep Instinct REST API. It is provided AS-IS/NO WARRANTY. It has
# limited error checking and logging, and likely contains defects or other
# deficiencies. Test thoroughly first, and use at your own risk. This API
# Wrapper is not a Deep Instinct commercial product and is not officially
# supported, althought he underlying REST API is. This means that to report an
# issue to tech support you must remove the API Wrapper layer and recreate the
# problem against the raw/pure DI REST API.
#

debug_mode = False

# Import various libraries used by one or more method below.
import requests, json, datetime, pandas, re, ipaddress, time, os
#If any of the above throw import errors, try running 'pip install library_name'
#If that doesn't fix the problem I recommend to search Google for the error
#that you are getting.

# Export Device List to disk in Excel format
def export_devices(include_deactivated=False):
    #get the devices from server
    devices = get_devices(include_deactivated=include_deactivated)
    #convert to Pandas Data Frame
    devices_df = pandas.DataFrame(devices)
    #calculate timestamp
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d_%H.%M')
    #calculate folder name
    folder_name = create_export_folder()
    #calculate file name
    file_name = f'device_list_{timestamp}_{fqdn.split(".",1)[0]}.xlsx'
    #write data to disk
    devices_df.to_excel(f'{folder_name}/{file_name}', index=False)
    #return confirmation message
    print (f'INFO: {str(len(devices))} devices exported to {folder_name}/{file_name}')


# Accepts a list of (exact hostnames | hostname regex patterns | CIDRs) and
# a group name. Finds matching devices and matching group, then moves the
# devices to that group. Note that even when using exact hostnames, there
# may be multiple matches found, and in that case all will be moved.
def move_devices(search_list, group_name, regex_hostname_search=False, cidr_search=False):
    # Get device IDs
    device_ids = get_device_ids(search_list=search_list, regex_hostname_search=regex_hostname_search, cidr_search=cidr_search)
    # Lookup to get Device Group ID
    group_id = get_group_id(group_name=group_name, exclude_default_groups=True)
    # Execute the move
    return add_devices_to_group(device_ids=device_ids, group_id=group_id) + ' ' + group_name


# Accepts list of hostnames, removes any explicit/manual group assignment.
def move_devices_to_automatic_assignment(hostnames):
    #Get all devices from server
    devices = get_devices(include_deactivated=False)

    #Establish a list to store the devices that match the search list
    devices_to_move = []

    #Search the full device list and pull out those that match our search list
    for device in devices:
        if device['hostname'] in hostnames:
            devices_to_move.append(device)

    #Iterate through the list of matching devices
    for device in devices_to_move:
        #Remove the device from it's current group
        remove_devices_from_group([device['id']], device['group_id'])

    #Return a message indicating how many devices were moved
    return(str(len(devices_to_move)) + ' devices were moved to automatic assignment')


#Archives (hides from GUI and API) a list of devices
def archive_devices(device_ids, unarchive=False):
    # Calculate headers and URL
    headers = {'Content-Type': 'application/json', 'Authorization': key}
    if unarchive:
        request_url = f'https://{fqdn}/api/v1/devices/actions/unarchive'
    else:
        request_url = f'https://{fqdn}/api/v1/devices/actions/archive'

    # Create payload with list of provided IDs as a Python dictionary
    payload = {'ids': device_ids}

    # Send request to server
    response = requests.post(request_url, json=payload, headers=headers)

    # Check response code
    if response.status_code == 200:
        # return True if operation was successful
        return True
    else:
        # return False if unexpected return code (something failed)
        return False


# Unarchives (unhides from GUI and API) a list of devices
def unarchive_devices(device_ids):
    return archive_devices(device_ids=device_ids, unarchive=True)


# Write Device Policy data to disk in MS Excel format.
def export_policies(include_allow_deny_lists=True):
    # Get all policies from server, including auxilary data
    policies = get_policies(include_policy_data=True, include_allow_deny_lists=include_allow_deny_lists)

    # Divide the policies into platform-specific lists
    # --> This is done for purposes of cleaner/more usable exports, since
    #     different platform policies have different columns of data.
    windows_policies = []
    mac_policies = []
    ios_policies = []
    android_policies = []
    chrome_policies = []
    network_agentless_policies = []
    linux_policies = []
    for policy in policies:
        if policy['os'] == 'WINDOWS':
            windows_policies.append(policy)
        elif policy['os'] == 'MAC':
            mac_policies.append(policy)
        elif policy['os'] == 'ANDROID':
            android_policies.append(policy)
        elif policy['os'] == 'IOS':
            ios_policies.append(policy)
        elif policy['os'] == 'NETWORK_AGENTLESS':
            network_agentless_policies.append(policy)
        elif policy['os'] == 'LINUX':
            linux_policies.append(policy)

    #create dataframes to allow subsequent export to Excel
    windows_policies_df = pandas.DataFrame(windows_policies)
    mac_policies_df = pandas.DataFrame(mac_policies)
    ios_policies_df = pandas.DataFrame(ios_policies)
    android_policies_df = pandas.DataFrame(android_policies)
    chrome_policies_df = pandas.DataFrame(chrome_policies)
    network_agentless_policies_df = pandas.DataFrame(network_agentless_policies)
    linux_policies_df = pandas.DataFrame(linux_policies)

    #export dataframes to disk
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d_%H.%M')
    folder_name = create_export_folder()
    file_name = f'deepinstinct_policies_{timestamp}_{fqdn.split(".",1)[0]}.xlsx'
    with pandas.ExcelWriter(f'{folder_name}/{file_name}') as writer:
        windows_policies_df.to_excel(writer, sheet_name='Windows', index=False)
        mac_policies_df.to_excel(writer, sheet_name='macOS', index=False)
        ios_policies_df.to_excel(writer, sheet_name='iOS', index=False)
        android_policies_df.to_excel(writer, sheet_name='Android', index=False)
        chrome_policies_df.to_excel(writer, sheet_name='Chrome OS', index=False)
        linux_policies_df.to_excel(writer, sheet_name='Linux', index=False)
        network_agentless_policies_df.to_excel(writer, sheet_name='Agentless', index=False)
    print(f'INFO: {str(len(policies))} policies exported to {folder_name}/{file_name}')

# Enable automatic upgrade setting in policies
def enable_upgrades(platforms=['WINDOWS','MAC'], automatic_upgrade=True, return_modified_policies_id_list=False):
    # Get list of policies
    policies = get_policies()

    # Establish a counter of how many policies were modified (used in return)
    modified_policy_counter = 0

    # Establish a list of modified policy IDs
    modified_policies_id_list = []

    # Static headers for all requests in this function
    headers = {'accept': 'application/json', 'Authorization': key}

    # Iterate through the polic0ies
    for policy in policies:
        # Check if the OS of the current policy is one of the targeted platforms
        if policy['os'] in platforms:
            # If yes, get policy data from the server
            policy_id = policy['id']
            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/data'
            response = requests.get(request_url, headers=headers)
            policy_data = response.json()
            # Check if the upgrade setting needs changing
            if policy_data['data']['automatic_upgrade'] != automatic_upgrade:
                # If yes, set it to desired setting
                policy_data['data']['automatic_upgrade'] = automatic_upgrade
                # Write modified policy data back to server (saving change)
                response = requests.put(request_url, json=policy_data, headers=headers)
                # Increment the counter of how many policies we have modified
                modified_policy_counter += 1
                modified_policies_id_list.append(policy['id'])

    return_string = str(modified_policy_counter) + ' policies modified to set automatic_upgrade to ' + str(automatic_upgrade)

    if return_modified_policies_id_list:
        print(return_string)
        return modified_policies_id_list
    else:
        return return_string


# Disable automatic upgrade setting in policies
def disable_upgrades(platforms=['WINDOWS','MAC'], return_modified_policies_id_list=False):
    return enable_upgrades(platforms=platforms, automatic_upgrade=False, return_modified_policies_id_list=return_modified_policies_id_list)


# Enables upgrades for a list of policy IDs
def enable_upgrades_for_list_of_policy_ids(policy_ids, automatic_upgrade=True):

    # Establish a counter of how many policies were modified (used in return)
    modified_policy_counter = 0

    # Static headers for all requests in this function
    headers = {'accept': 'application/json', 'Authorization': key}

    # Iterate through the poliocy ids provided
    for policy_id in policy_ids:
        request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/data'
        response = requests.get(request_url, headers=headers)
        policy_data = response.json()
        # Check if the upgrade setting needs changing
        if policy_data['data']['automatic_upgrade'] != automatic_upgrade:
            # If yes, set it to desired setting
            policy_data['data']['automatic_upgrade'] = automatic_upgrade
            # Write modified policy data back to server (saving change)
            request = requests.put(request_url, json=policy_data, headers=headers)
            # Increment the counter of how many policies we have modified
            modified_policy_counter += 1

    return str(modified_policy_counter) + ' policies modified to set automatic_upgrade to ' + str(automatic_upgrade)


# Returns list of visible Tenants
def get_tenants():
    #get data
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/multitenancy/tenant/'
    response = requests.get(request_url, headers=headers)

    #return data
    if response.status_code == 200:
        #return list of tenants
        return response.json()['tenants']
    else:
        #in case of error return an empty list
        return []


# Returns a list of all visible Devices
def get_devices(include_deactivated=True):
    # CREATE VARIABLES
    #cursor to keep track of highest device id returned
    last_id = 0
    #list to collect the devices
    collected_devices = []
    #static set of headers for requests in this method
    headers = {'accept': 'application/json', 'Authorization': key}

    # The method we are using (/api/v1/devices) returns up to 50 devices at a
    # time, and the response includes a last_id which indicates the highest
    # device id returned. We will know we have all devices visible to our API
    # key when we get last_id=None in a response.

    error_count = 0
    # COLLECT DATA
    while last_id != None and error_count < 10: #loop until all visible devices have been collected
        #calculate URL for request
        request_url = f'https://{fqdn}/api/v1/devices?after_device_id={last_id}'
        #make request, store response
        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            response = response.json() #convert to Python list
            if 'last_id' in response:
                last_id = response['last_id'] #save returned last_id for reuse on next request
            else: #added this to handle issue where some server versions fail to return last_id on final batch of devices
                last_id = None
            print(request_url, 'returned 200 with last_id', last_id, end='\r')
            if 'devices' in response:
                devices = response['devices'] #extract devices from response
                for device in devices: #iterate through the list of devices
                    if device['license_status'] == 'ACTIVATED' or include_deactivated:
                        collected_devices.append(device) #add to collected devices
        else:
            print('WARNING: Unexpected return code', response.status_code,
            'on request to\n', request_url, '\nwith headers\n', headers)
            error_count += 1  #increment error counter
            time.sleep(10) #wait before trying request again
    print('\n')

    # When while loop exists, we know we have collected all visible data

    # RETURN COLLECTED DATA
    return collected_devices


# Translates a list of device names, regex patterns, or CIDRs to a list of
# device IDs
def get_device_ids(search_list, regex_hostname_search=False, cidr_search=False):
    # GET ALL DEVICES
    devices = get_devices(include_deactivated=False)

    # CREATE A LIST TO COLLECT SEARCH RESULTS
    device_ids = []

    # ITERATE THROUGH THE DEVICES, COLLECT MATCHES

    # Regex-based matching on hostname
    if regex_hostname_search:
        for device in devices:
            for regex in search_list: #for each regex...
                if re.match(regex, device['hostname']): #check if hostname matches
                    if device['id'] not in device_ids: #avoid duplicates
                        device_ids.append(device['id']) #append id to search results

    # IP range (CIDR) matching
    elif cidr_search:
        for cidr in search_list: #for each cidr in the search list...
            for device in devices:
                if ipaddress.ip_address(device['ip_address']) in ipaddress.ip_network(cidr):
                    if device['id'] not in device_ids: #avoid duplicates
                        device_ids.append(device['id']) #append id to search results

    # Hostname search (exact match only)
    else:
        for device in devices:
            if device['hostname'] in search_list:
                device_ids.append(device['id']) #append id to search results

    # RETURN THE SEARCH RESULTS
    return device_ids


# Translate a Device Group name into a Device Group IP
def get_group_id(group_name, exclude_default_groups=False):

    # Get the groups from the server
    groups = get_groups(exclude_default_groups=exclude_default_groups)

    #Iterate through the groups looking for match on group name
    for group in groups:
        if group['name'].lower() == group_name.lower():  #case-insensitive
            return group['id'] #match was found; return the id of that match
    return None #no match found


# Adds a list of Devices to a Device Group
def add_devices_to_group(device_ids, group_id, remove=False):
    # Calculate headers and URL
    headers = {'Content-Type': 'application/json', 'Authorization': key}
    if remove:
        request_url = f'https://{fqdn}/api/v1/groups/{group_id}/remove-devices'
    else:
        request_url = f'https://{fqdn}/api/v1/groups/{group_id}/add-devices'

    # Create payload
    payload = {'devices': device_ids}

    # Send to server, return confirmation if successful
    response = requests.post(request_url, json=payload, headers=headers)
    if response.status_code == 204: #expected return code
        if remove:
            return str(len(device_ids)) + ' devices removed from group ' + str(group_id)
        else:
            return str(len(device_ids)) + ' devices added to group ' + str(group_id)
    else:
        return None #something went wrong


# Removes a list of Devices from a Device Group
def remove_devices_from_group(device_ids, group_id):
    return add_devices_to_group(device_ids=device_ids, group_id=group_id, remove=True)


# Collect and return list of Device Policies.
def get_policies(include_policy_data=False, include_allow_deny_lists=False, keep_data_encapsulated=False, msp_id='ALL'):
    # GET POLICIES (basic data only)

    # Calculate headers and URL
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/policies/'

    # Get data, convert to Python list
    response = requests.get(request_url, headers=headers)
    policies = response.json()

    # Apply filter based on msp, if enabled
    if msp_id != 'ALL':
        filtered_policies = []
        for policy in policies:
            if policy['msp_id'] == msp_id:
                filtered_policies.append(policy)
        policies = filtered_policies

    # APPEND POLICY DATA (IF ENABLED)
    if include_policy_data:

        # Iterate through policy list
        for policy in policies:
            # Extract ID, calculate URL, and pull policy data from server
            policy_id = policy['id']
            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/data'
            response = requests.get(request_url, headers=headers)
            print(request_url, 'returned', response.status_code, end='\r')
            # Check response code (for some platforms, no policy data available)
            if response.status_code == 200:
                # Extract policy data from response and append it to policy
                if keep_data_encapsulated:
                    policy_data = response.json()
                else:
                    policy_data = response.json()['data']
                policy.update(policy_data)
        print('\n')

    # APPEND ALLOW-LIST, DENY-LIST, AND EXCLUSION DATA (IF ENABLED)
    if include_allow_deny_lists:

        allow_deny_and_exclusion_list_types = [
            'allow-list/hashes',
            'allow-list/paths',
            'allow-list/certificates',
            'allow-list/process_paths',
            'allow-list/scripts',
            'deny-list/hashes',
            'exclusion-list/folder_path',
            'exclusion-list/process_path'
        ]

        # Iterate through policy list
        for policy in policies:

            # Extract the policy id, which is used in subsequent requests
            policy_id = policy['id']

            #create a dictionary in the policy to store this data
            policy['allow_deny_and_exclusion_lists'] = {}

            #iterate through list types to migrate
            for list_type in allow_deny_and_exclusion_list_types:

                request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/{list_type}'
                response = requests.get(request_url, headers=headers)
                print(request_url, 'returned', response.status_code, end='\r')
                if response.status_code == 200:
                    response = response.json()
                    policy['allow_deny_and_exclusion_lists'][list_type] = response
        print('\n')

    # RETURN THE COLLECTED DATA
    return policies


# Returns list of visible MSPs
def get_msps():
    #get data
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/multitenancy/msp/'
    response = requests.get(request_url, headers=headers)

    #return data
    if response.status_code == 200:
        #return list of msps
        return response.json()['msps']
    else:
        #in case of error return an empty list
        return []


# Create a new MSP
def create_msp(msp_name, license_limit):
    # Calculate headers, URL, and payload
    headers = {'Content-Type': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/multitenancy/msp/'
    payload = {'name': msp_name, 'license_limit': license_limit}

    # Send request to server
    response = requests.post(request_url, json=payload, headers=headers)

    # Check return code and return Success or descriptive error
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 409:
        return 'ERROR: MSP name already exists'
    elif response.status_code == 401:
        return 'ERROR: Unauthorized'
    elif response.status_code == 400:
        return 'ERROR: Insufficient Licenses'
    else:
        return 'ERROR: Unexpected return code '+ str(response.status_code)


# Delete an MSP based on provided name
def delete_msp(msp_name):
    # Get the list of MSPs
    msps = get_msps()

    # Iterate through the list of MSPs looking for a match on the provided name
    msp_id = None
    for msp in msps:
        if msp['name'].lower() == msp_name.lower():
            msp_id = msp['id']
    if msp_id == None:
        return 'No match found for provided msp_name ' + msp_name

    # DELETE THE MSP
    request_url = f'https://{fqdn}/api/v1/multitenancy/msp/{msp_id}'
    headers = {'Authorization': key}
    response = requests.delete(request_url, headers=headers)

    # RETURN SUCCESS/FAILURE BASED ON RETURN CODE
    if response.status_code == 204:
        return 'MSP ' + str(msp_id) + ' ' + msp_name + ' was deleted'
    elif response.status_code == 409:
        return 'MSP ' + str(msp_id) + ' ' + msp_name + ' cannot be deleted because active devices still exist'
    elif response.status_code == 404:
        return 'MSP ' + str(msp_id) + ' ' + msp_name + ' was not found'
    elif response.status_code == 403:
        return 'MSP ' + str(msp_id) + ' ' + msp_name + ' cannot be deleted because only Hub-Admin can delete MSPs'
    else:
        return 'ERROR: Unexpected return code ' + str(response.status_code)

# Remotely uninstall a device
def remove_device(device, device_id_only=False):

    #PROCESS INPUT
    if device_id_only:
        #the input was the actual device id
        device_id = device
    else:
        #the input was a device dictionary; extract the device id from it
        device_id = device['id']

    #UNINSTALL THE DEVICE
    request_url = f'https://{fqdn}/api/v1/devices/{device_id}/actions/remove'
    headers = {'Authorization': key}
    response = requests.post(request_url, headers=headers)

    #RETURN TRUE/FALSE BASED ON WHETHER WE GOT THE EXPECTED RETURN CODE
    if response.status_code == 204:
        print('INFO: Successfully removed device', device)
        return True
    else:
        print('INFO: Failed to remove device', device)
        return False


# Return a list of events matching specified search parameters and/or minimum
# event id. If neither are provided, all visible events are returned.
def get_events(search={}, minimum_event_id=0, suspicious=False):

    #define HTTP headers for all requests in this method
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': key}

    #list to collect events
    collected_events = []

    #Note that the API method we are calling returns up to 50 events at a time,
    #and we know we have all events when we get last_id=None back in the response

    #loop until we have all the events
    while minimum_event_id != None:

        #calculate request url
        if suspicious:
            request_url = f'https://{fqdn}/api/v1/suspicious-events/search?after_event_id={str(minimum_event_id)}'
        else:
            request_url = f'https://{fqdn}/api/v1/events/search?after_event_id={str(minimum_event_id)}'

        #make request to server, store response
        response = requests.post(request_url, headers=headers, json=search)

        #check HTTP return code, and in case of error exit the method and return empty list
        if response.status_code != 200:
            print('ERROR:', request_url, 'returned unexpected response code:', response.status_code)
            return []
        else:
            #store the returned last_id value
            minimum_event_id = response.json()['last_id']

            #print result to console
            print(request_url, 'returned', response.status_code, 'with last_id', minimum_event_id, end='\r')

            #if we got a none-null last_id back
            if minimum_event_id != None:
                #then extract the events
                events = response.json()['events']
                #append the event(s) from this response to collected_events
                for event in events:
                    collected_events.append(event)
    print('\n')

    #return the list of collected events
    return collected_events


# Return a list of suspicious events matching specified search parameters
# and/or minimum event id. If neither are provided, all visible susipcious
# events are returned.
def get_suspicious_events(search={}, minimum_event_id=0):
    return get_events(suspicious=True, search=search, minimum_event_id=minimum_event_id)


#Return a list of all visible Device Groups
def get_groups(exclude_default_groups=False):
    # Calculate headers and URL
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/groups/'
    # Get Device Groups from server
    response = requests.get(request_url, headers=headers)
    #Check response code
    if response.status_code == 200:
        groups = response.json() #convert to Python list
        #optionally remove the default groups before returning the data
        if exclude_default_groups:
            #Note [:]: syntax on line below to make a copy of list before iterating over it sincer we're going to be removing elements, as per https://stackoverflow.com/questions/7210578/why-does-list-remove-not-behave-as-one-might-expect
            for group in groups[:]:
                if group['is_default_group']:
                    groups.remove(group)
        return groups
    else:
        #in case of error getting data, return empty list
        return []

#Gets a single device
def get_device(device_id):
    # Calculate headers and URL
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/devices/{device_id}'
    # Get data on the requested device ID from the server
    response = requests.get(request_url, headers=headers)
    # Check response code
    if response.status_code == 200:
        device = response.json() #convert to Python list
        return device
    else:
        #in case of error getting data, return None
        return None

#hides a list of event ids from the GUI and REST API
def archive_events (event_id_list, unarchive=False, suspicious=False, input_is_ids_only=True):

    # if full events were provided, strip out just the ids before proceeding
    if not input_is_ids_only:
        event_ids = []
        for event in event_id_list:
            event_ids.append(event['id'])
        event_id_list = event_ids

    # set headers (same for all requests in this method)
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': key}

    # Create payload with list of event IDs as a Python dictionary
    payload = {'ids': event_id_list}

    # calculate the appropriate url based on configuration
    if not suspicious and not unarchive:
        request_url = f'https://{fqdn}/api/v1/events/actions/archive'
    elif not suspicious and unarchive:
        request_url = f'https://{fqdn}/api/v1/events/actions/unarchive'
    elif suspicious and not unarchive:
        request_url = f'https://{fqdn}/api/v1/suspicious-events/actions/archive'
    elif suspicious and unarchive:
        request_url = f'https://{fqdn}/api/v1/suspicious-events/actions/unarchive'

    #send request to server
    response = requests.post(request_url, headers=headers, json=payload)

    #return true if successful, false otherwise
    return (response.status_code == 204)


#hides a list of suspicious event ids from the GUI and REST API
def archive_suspicious_events(event_id_list, unarchive=False, input_is_ids_only=True):
    return archive_events(event_id_list=event_id_list, suspicious=True)


#unhides a list of event ids from the GUI and REST API
def unarchive_events(event_id_list, suspicious=False, input_is_ids_only=True):
    return archive_events(event_id_list=event_id_list, unarchive=True, suspicious=suspicious, input_is_ids_only=input_is_ids_only)


#unhides a list of suspicious event ids from the GUI and REST API
def unarchive_suspicious_events(event_id_list, input_is_ids_only=True):
    return unarchive_events(event_id_list=event_id_list, suspicious=True, input_is_ids_only=input_is_ids_only)


#allows organization of exported data by server-specific folders
def create_export_folder():
    exported_data_folder_name = f'exported_data_from_{fqdn}'
    # Check if a folder already exists for data exports from this server
    if not os.path.exists(exported_data_folder_name):
        # ...If not, then create it
        os.makedirs(exported_data_folder_name)
    return exported_data_folder_name

def get_event(event_id, suspicious=False):

    #define headers
    headers = {'accept': 'application/json', 'Authorization': key}

    #calculate request url
    if suspicious:
        request_url = f'https://{fqdn}/api/v1/suspicious-events/{str(event_id)}'
    else:
        request_url = f'https://{fqdn}/api/v1/events/{str(event_id)}'

    #make request, store response
    response = requests.get(request_url, headers=headers)

    # based on response code, return event or alternately an error code
    if response.status_code == 200:
        return response.json()['event']
    elif response.status_code == 404:
        print('ERROR: Event', str(event_id), 'not found')
        return []
    else:
        print('ERROR: Unexpected return code', str(response.status_code), 'on request to', request_url)
        return []

def create_policy(name, base_policy_id, comment='', quiet_mode=False):

    #define headers
    headers = {'accept': 'application/json', 'Authorization': key}

    #calculate request url
    request_url = f'https://{fqdn}/api/v1/policies/'

    #create the payload
    payload = {'name': name, 'comment': comment, 'base_policy_id': base_policy_id}

    # Send request to server
    response = requests.post(request_url, json=payload, headers=headers)

    # Check response code
    if response.status_code == 200:
        response = response.json()
        if not quiet_mode:
            print('INFO: Policy', response['id'], response['name'], 'created')
        return response
    else:
        print('ERROR: Unexpected return code', response.status_code,
        'on POST to', request_url, 'with payload\n', payload)
        return None

def delete_policy(policy_id):

    #define headers
    headers = {'accept': 'application/json', 'Authorization': key}

    #calculate request url
    request_url = f'https://{fqdn}/api/v1/policies/{policy_id}'

    # Send request to server
    response = requests.delete(request_url, headers=headers)

    # Check response code
    if response.status_code == 204:
        print('INFO: Policy', policy_id, 'was deleted')
        return True
    elif response.status_code == 404:
        print('ERROR: Policy', policy_id, 'not found')
        return False
    elif response.status_code == 422:
        print('ERROR: Policy', policy_id, 'is a default policy. Default policies cannot be deleted.')
        return False
    else:
        print('ERROR: Unexpected return code', response.status_code,
        'on DELETE to', request_url)
        return False

def export_events(minimum_event_id=0, suspicious=False, flatten_device_info=True):

    events = get_events(minimum_event_id=minimum_event_id, suspicious=suspicious)

    if len(events) > 0:
        if flatten_device_info:
            #flattens recorded_device_info into discreet columns. Examples: recorded_device_info.hostname, recorded_device_info.policy_name
            events = pandas.json_normalize(events)
        events_df = pandas.DataFrame(events)
        events_df.sort_values(by=['id'], inplace=True)
        folder_name = create_export_folder()
        file_name = f'events_{datetime.datetime.today().strftime("%Y-%m-%d_%H.%M")}_{fqdn.split(".",1)[0]}.xlsx'
        if suspicious:
            file_name = f'suspicious_{file_name}'

        #this logic improves resiliency case the product API adds/removes columns from event data
        export_column_names = ['id', 'status', 'action', 'type', 'trigger', 'threat_severity', 'file_hash', 'deep_classification', 'file_archive_hash', 'path', 'timestamp', 'insertion_timestamp', 'close_timestamp', 'close_trigger', 'last_reoccurrence', 'reoccurrence_count', 'last_action', 'device_id', 'recorded_device_info.os', 'recorded_device_info.mac_address', 'recorded_device_info.hostname', 'recorded_device_info.tag', 'recorded_device_info.group_name', 'recorded_device_info.policy_name', 'recorded_device_info.tenant_name', 'comment', 'mitre_classifications', 'file_size', 'file_status', 'sandbox_status', 'msp_name', 'msp_id', 'tenant_name', 'tenant_id']
        events_df_column_names = list(events_df.columns.values)
        columns = []
        for column_name in export_column_names:
            if column_name in events_df_column_names:
                columns.append(column_name)

        #now that we have what we know is a valid list of coulmns, proceed
        events_df.to_excel(f'{folder_name}/{file_name}', index=False, sheet_name='Event_Data', columns=columns)
        print (f'INFO: {str(len(events))} events exported to {folder_name}/{file_name}')
    else:
        print('WARNING: No events were found on the server')

def export_groups(exclude_default_groups=False):
    groups = get_groups(exclude_default_groups=exclude_default_groups)
    groups_df = pandas.DataFrame(groups)
    folder_name = create_export_folder()
    file_name = f'groups_{datetime.datetime.today().strftime("%Y-%m-%d_%H.%M")}_{fqdn.split(".",1)[0]}.xlsx'
    groups_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print (f'INFO: {str(len(groups))} groups exported to {folder_name}/{file_name}')


def create_tenant(tenant_name, license_limit, msp_name):

    #convert provided msp_name to msp_id
    msp_id = get_msp_id(msp_name)

    #build payload
    payload = {'msp_id': msp_id,
                'name': tenant_name,
                'license_limit': license_limit }

    #calculate headers
    headers = {'Content-Type': 'application/json', 'Authorization': key}

    #calculate URL
    request_url = f'https://{fqdn}/api/v1/multitenancy/tenant/'

    # Send request to server
    response = requests.post(request_url, json=payload, headers=headers)

    # Check return code and return success or descriptive error
    if response.status_code == 200: #tenant creation was successful
        #return value is not particularily useful, therefore we will go
        #find the newly-created tenant in the full tenants list first so that
        #we can return a more meaningful/useful value with things like id
        #and activation tokens
        tenants = get_tenants()
        for tenant in tenants:
            if tenant['name'] == tenant_name and tenant['msp_id'] == msp_id:
                tenant['msp_name'] = msp_name
                return tenant
    else:
        return None


def get_msp_id(msp_name):
    msp_id = 0
    msps = get_msps()
    for msp in msps:
        if msp['name'] == msp_name:
            msp_id = msp['id']
    return msp_id


def delete_tenant(tenant_name, msp_name):

    #convert provided msp_name to msp_id
    msp_id = get_msp_id(msp_name)

    #find tenant id
    tenants = get_tenants()
    tenant_id = 0
    for tenant in tenants:
        if tenant['msp_id'] == msp_id:
            if tenant['name'] == tenant_name:
                tenant_id = tenant['id']

    #calculate URL and headers
    request_url = f'https://{fqdn}/api/v1/multitenancy/tenant/{tenant_id}'
    headers = {'Authorization': key}

    #send request to server
    response = requests.delete(request_url, headers=headers)

    # Check return code and return Success or descriptive error
    if response.status_code == 204:
        print('INFO: Tenant', tenant_name, 'was deleted from MSP', msp_name)
        return True
    elif response.status_code == 403:
        print('ERROR: Only Hub-Admin or MSP-Admin can delete tenants')
        return False
    elif response.status_code == 404:
        print('ERROR: Tenant not found')
        return False
    elif response.status_code == 409:
        print('ERROR: Tried to delete a tenant but active devices still exist!')
        return False

def request_agent_logs(device_id, device_id_only=True):

    if not device_id_only:
        device_id = device_id['id']

    #calculate URL and headers
    request_url = f'https://{fqdn}/api/v1/devices/{device_id}/actions/upload-logs'
    headers = {'Authorization': key, 'accept': 'application/json'}

    # Send request to server
    response = requests.post(request_url, headers=headers)

    # Check return code and return Success or descriptive error
    if response.status_code == 204:
        print('INFO: Device', device_id, 'set to upload logs')
        return True
    elif response.status_code == 403:
        print('WARN: Device', device_id, 'does not belong to connector’s msp')
        return False
    elif response.status_code == 404:
        print('WARN: Device', device_id, 'not found')
        return False
    else:
        print('ERROR: Unexpected return code', response.status_code, 'on POST to', request_url, 'with headers', headers)
        return False

def close_events(event_id_list, open=False, suspicious=False):

    #calculate URL
    if suspicious:
        if open:
            request_url = f'https://{fqdn}/api/v1/suspicious-events/actions/open'
        else:
            request_url = f'https://{fqdn}/api/v1/suspicious-events/actions/close'
    else:
        if open:
            request_url = f'https://{fqdn}/api/v1/events/actions/open'
        else:
            request_url = f'https://{fqdn}/api/v1/events/actions/close'

    #calculate headers and payload
    headers = {'Authorization': key,
                'accept': 'application/json',
                'Content-Type': 'application/json'}
    payload = {'ids': event_id_list}

    # Send request to server
    response = requests.post(request_url, json=payload, headers=headers)

    # Check return code and return Success or descriptive error
    if response.status_code == 204:
        if open:
            print('INFO:', len(event_id_list), 'events were opened')
        else:
            print('INFO:', len(event_id_list), 'events were closed')
        return True
    else:
        print('ERROR: Unexpected return code', response.status_code, 'on POST to', request_url)
        return False

def close_suspicious_events(event_id_list):
    return close_events(event_id_list=event_id_list, suspicious=True)

def open_events(event_id_list, suspicious=False):
    return close_events(event_id_list=event_id_list, open=True, suspicious=suspicious)

def open_suspicious_events(event_id_list):
    return open_events(event_id_list=event_id_list, suspicious=True)

def archive_events(event_id_list, unarchive=False, suspicious=False):

    #calculate URL
    if suspicious:
        if unarchive:
            request_url = f'https://{fqdn}/api/v1/suspicious-events/actions/unarchive'
        else:
            request_url = f'https://{fqdn}/api/v1/suspicious-events/actions/archive'
    else:
        if unarchive:
            request_url = f'https://{fqdn}/api/v1/events/actions/unarchive'
        else:
            request_url = f'https://{fqdn}/api/v1/events/actions/archive'

    #calculate headers and payload
    headers = {'Authorization': key,
                'accept': 'application/json',
                'Content-Type': 'application/json'}
    payload = {'ids': event_id_list}

    # Send request to server
    response = requests.post(request_url, json=payload, headers=headers)

    # Check return code and return Success or descriptive error
    if response.status_code == 204:
        if unarchive:
            print('INFO: Successfully unarchived up to ', len(event_id_list), 'events')
        else:
            print('INFO: Successfully archived up to ', len(event_id_list), 'events')
        return True
    else:
        print('ERROR: Unexpected return code', response.status_code, 'on POST to', request_url)
        return False

# Disable scanning and enforcement on a device
def disable_device(device, device_id_only=False):

    #PROCESS INPUT
    if device_id_only:
        #the input was the actual device id
        device_id = device
    else:
        #the input was a device dictionary; extract the device id from it
        device_id = device['id']

    #DISABLE THE DEVICE
    request_url = f'https://{fqdn}/api/v1/devices/{device_id}/actions/disable'
    headers = {'Authorization': key}
    response = requests.post(request_url, headers=headers)

    #RETURN TRUE/FALSE BASED ON WHETHER WE GOT THE EXPECTED RETURN CODE
    if response.status_code == 204:
        print('INFO: Successfully set device', device, 'to be disabled')
        return True
    else:
        print('INFO: Failed to disable device', device)
        return False


# Enable scanning and enforcement on a device
def enable_device(device, device_id_only=False):

    #PROCESS INPUT
    if device_id_only:
        #the input was the actual device id
        device_id = device
    else:
        #the input was a device dictionary; extract the device id from it
        device_id = device['id']

    #ENABLE THE DEVICE
    request_url = f'https://{fqdn}/api/v1/devices/{device_id}/actions/enable'
    headers = {'Authorization': key}
    response = requests.post(request_url, headers=headers)

    #RETURN TRUE/FALSE BASED ON WHETHER WE GOT THE EXPECTED RETURN CODE
    if response.status_code == 204:
        print('INFO: Successfully set device', device, 'to be enabled')
        return True
    else:
        print('INFO: Failed to enable device', device)
        return False


def get_event_counts_by_device_id(minimum_event_id=0, event_filters={}):

    #get event data from server
    events = get_events(minimum_event_id=minimum_event_id, search=event_filters)

    #convert to PivotTable style summary of event count by device id
    event_counts = count_data_by_field(events, 'device_id')

    #return the data
    return event_counts


def export_event_count_by_device_id(minimum_event_id=0, event_filters={}):

    #get events counts
    event_counts = get_event_counts_by_device_id(minimum_event_id=minimum_event_id, event_filters=event_filters)

    #above returns a dictionary; the syntax below flattens this into a 2-column dataframe
    event_counts_df = pandas.DataFrame(list(event_counts.items()),columns = ['device_id','event_count'])

    #sort data with highest event count on top
    event_counts_df.sort_values(by=['event_count'], ascending=False, inplace=True)

    #calculate (and create if necessary) export folder and file name
    folder_name = create_export_folder()
    file_name = f'event_count_by_device_id_{datetime.datetime.today().strftime("%Y-%m-%d_%H.%M")}_{fqdn.split(".",1)[0]}.xlsx'

    #write data to disk
    event_counts_df.to_excel(f'{folder_name}/{file_name}', index=False, sheet_name='Event_Counts')
    print('INFO: event counts were exported to disk as:', f'{folder_name}/{file_name}')

    #return event_counts in case needed for further analysis in another method
    return event_counts

def count_data_by_field(data, field_name):
    result = {}
    for record in data:
        if record[field_name] in result.keys():
            result[record[field_name]] += 1
        else:
            result[record[field_name]] = 1
    return result

def is_prevention_policy(policy, exclude_static_analysis=False, exclude_ransomware_behavior=False, exclude_remote_code_injection=False, exclude_arbritrary_shallcode_execution=False):

    verdict = False #start with false until proven otherwise

    #For windows, require that all [currently exposed] features that Best Practices call for general usage be in prevention
    if policy['os'] == 'WINDOWS':
        if policy['prevention_level'] in ('LOW', 'MEDIUM') or exclude_static_analysis:
            if policy['ransomware_behavior'] == 'PREVENT' or exclude_ransomware_behavior:
                if policy['remote_code_injection'] == 'PREVENT' or exclude_remote_code_injection:
                    if policy['arbitrary_shellcode_execution'] == 'PREVENT' or exclude_arbritrary_shallcode_execution:
                        verdict = True

    #This covers all non-Windows platforms that have a prevention threshold (current and future)
    elif 'prevention_level' in policy.keys():
        if policy['prevention_level'] in ('LOW', 'MEDIUM', 'HIGH') or exclude_static_analysis:
            verdict = True

    return verdict

def download_uploaded_file(file_hash):
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/events/actions/download-uploaded-file/{file_hash}'
    response = requests.get(request_url, headers=headers)
    if response.status_code == 200:
        folder_name = create_export_folder()
        file_name = f'{file_hash}.zip'
        open(f'{folder_name}/{file_name}','wb').write(response.content)
        return True
    else:
        print('ERROR: Unexpected status code', response.status_code, 'on GET', request_url)
        return False

def request_malware_sample(event_id):

    #calculate URL and headers
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/devices/actions/request-remote-file-upload/{event_id}'

    # Send request to server
    response = requests.post(request_url, headers=headers)

    # Check return code and return Success or descriptive error
    if response.status_code == 204:
        print('INFO: Upload of malware sample for event', event_id, 'successfully queued')
        return True
    elif response.status_code == 404:
        print('WARN: Event', event_id, 'not found')
        return False
    else:
        print('ERROR: Unexpected return code', response.status_code, 'on POST to', request_url, 'with headers', headers)
        return False

def isolate_from_network(devices, release_from_isolation=False, input_is_hostnames=True):

    if input_is_hostnames:
        device_ids = get_device_ids(search_list=devices)
    else:
        device_ids = devices

    if not remove_from_isolation:
        request_url = f'https://{fqdn}/api/v1/devices/actions/isolate-from-network'
    else:
        request_url = f'https://{fqdn}/api/v1/devices/actions/release-from-isolation'

    headers = {'accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': key}
    payload = {'ids': device_ids}

    response = requests.post(request_url, headers=headers, json=payload)

    if response.status_code == 200:
        if remove_from_isolation:
            print('INFO: Removed', len(device_ids), 'devices from network isolation')
        else:
            print('INFO: Network isolated', len(device_ids), 'devices')
        return True
    else:
        print('ERROR: Unexpected return code', response.status_code,
                'on POST to', request_url, 'with payload', payload)
        return False


def remove_from_isolation(device_ids, input_is_hostnames=True):
    return isolate_from_network(device_ids=device_ids, release_from_isolation=True, input_is_hostnames=input_is_hostnames)


def add_hashes_to_deny_list(hash_list, policy_id=0, all_policies=False, platforms=['WINDOWS','MAC','LINUX','NETWORK_AGENTLESS']):

    policies = get_policies(include_policy_data=False)
    policy_id_list = []
    for policy in policies:
        if policy['os'] in platforms:
            if all_policies or policy['id'] == policy_id:
                policy_id_list.append(policy['id'])

    payload = {'items:': []}
    for hash in hash_list:
        payload_entry = {'item': hash, 'comment': 'Deny Listed by di.add_hashes_to_deny_list'}
        payload['items'].append(payload_entry)

    headers = {'accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': key}

    error_count = 0
    for policy_id in policy_id_list:
        request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/deny-list/hashes'
        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 204:
            print('INFO: Successfully added', len(payload['items']), 'hashes to the deny list for policy', policy_id)
        else:
            print('ERROR: Unexpected return code', response.status_code, 'on POST to', request_url)
            error_count += 1
    if error_count > 0:
        return False
    else:
        return True

# Method to copy policies from one MSP to another on a multi-tenancy server
def migrate_policies(source_msp_id, destination_msp_id, platforms_to_migrate=['WINDOWS', 'MAC'], allow_deny_and_exclusion_list_types = ['allow-list/hashes', 'allow-list/paths', 'allow-list/certificates', 'allow-list/process_paths', 'allow-list/scripts', 'deny-list/hashes', 'exclusion-list/folder_path', 'exclusion-list/process_path'] ):

    #get policies from each of the MSPs
    source_msp_policies = get_policies(include_policy_data=True, keep_data_encapsulated=True, include_allow_deny_lists=True, msp_id=source_msp_id)
    destination_msp_policies = get_policies(include_policy_data=True, keep_data_encapsulated=True, include_allow_deny_lists=True, msp_id=destination_msp_id)

    #build list of policy names in destination MSP (so as to avoid collissions)
    destination_msp_policy_names = []
    for policy in destination_msp_policies:
        destination_msp_policy_names.append(policy['name'])

    #build a dictionary of default policy IDs in destination MSP (used for policy creation)
    destination_default_policy_ids = {}
    for policy in destination_msp_policies:
        if policy['is_default_policy']:
            destination_default_policy_ids[policy['os']] = policy['id']

    #build list of policies to migrate
    policies_to_migrate = []
    for source_msp_policy in source_msp_policies:
        if source_msp_policy['os'] in platforms_to_migrate:
            policies_to_migrate.append(source_msp_policy)

    #Migrate the policies
    for policy in policies_to_migrate:

        #first step is to create the base policy, which we'll base on the platform-specific default policy
        if policy['name'] in destination_msp_policy_names:
            for destination_msp_policy in destination_msp_policies:
                if policy['name'] == destination_msp_policy['name']:
                    new_policy = destination_msp_policy
        else:
            new_policy = create_policy(policy['name'], destination_default_policy_ids[policy['os']], quiet_mode=True, )

        #next step is to overwrite the policy data on the newly-create policy with data from source policy
        new_policy_id = new_policy['id']
        request_url = f'https://{fqdn}/api/v1/policies/{new_policy_id}/data'
        headers = {'accept': 'application/json', 'Authorization': key}
        payload = {'data': policy['data']}
        response = requests.put(request_url, json=payload, headers=headers)
        if response.status_code != 204:
            print('ERROR: Unexpected response', response.status_code, 'on PUT to', request_url)

        #last step is to migrate the associated allow list, deny list, and exclusion lists for the policy
        headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': key}
        for list_type in allow_deny_and_exclusion_list_types:
            if list_type in policy['allow_deny_and_exclusion_lists']:
                if len(policy['allow_deny_and_exclusion_lists'][list_type]['items']) > 0:
                    payload = policy['allow_deny_and_exclusion_lists'][list_type]
                    request_url = f'https://{fqdn}/api/v1/policies/{new_policy_id}/{list_type}'
                    response = requests.post(request_url, headers=headers, json=payload)
                    if response.status_code != 204:
                        print('ERROR: Unexpected response', response.status_code, 'on POST to', request_url, 'with payload', payload)

    print('INFO: Done migrating', len(policies_to_migrate), 'policies from MSP', source_msp_id , 'to MSP', destination_msp_id)

def health_check(minimum_event_id=0):
    export_devices()
    print()
    export_policies()
    print()
    export_groups()
    print()
    export_events(minimum_event_id=minimum_event_id)
    print()
    import warranty_compliance_check as wcs
    wcs.do_warranty_compliance_check(fqdn=fqdn, key=key, exclude_empty_policies=True)

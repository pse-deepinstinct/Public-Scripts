# Deep Instinct v2.5 REST API Wrapper for Python
# Patrick Van Zandt
#
# Compatibility:
# -Designed for and tested using Deep Instinct D-Appliance version 2.5.0.1
# -Written and tested using a Python 3.8.3 instance installed by Anaconda
#
# Suggested Usage:
# 1. Save this file as deepinstinct25.py in the same directory as your code
# 2. Include "import deepinstinct25 as di" at the top of your code
# 3. Set/modify the DI server name like this: di.fqdn = 'SERVER-NAME'
# 4. Set/modify the DI REST API key like this: di.key = 'API-KEY'
# 5. Invoke the REST API methods like this:  di.function_name(arg1, arg2)
# 6. For testing and interactive usage, I use and recommend Jupyter Notebook,
#    which is installed as part of Anaconda (https://www.anaconda.com/)
#

# Import various libraries used by one or more method below.
import requests, json, datetime, pandas, re, ipaddress, time, os
#If any of the above throw import errors, try running 'pip install library_name'
#If that doesn't fix the problem I recommend to search Google for the error
#that you are getting.


# Export Device List to disk in Excel format
def export_devices():
    #get the devices from server
    devices = get_devices()
    #convert to Pandas Data Frame
    devices_df = pandas.DataFrame(devices)
    #calculate timestamp
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d_%H.%M')
    #calculate folder name
    folder_name = create_export_folder()
    #calculate file name
    file_name = f'device_list_{timestamp}.xlsx'
    #write data to disk
    devices_df.to_excel(f'{folder_name}/{file_name}', index=False)
    #return confirmation message
    return ('INFO: ' + str(len(devices)) + f' devices written to {folder_name}/{file_name}')


# Accepts a list of (exact hostnames | hostname regex patterns | CIDRs) and
# a group name. Finds matching devices and matching group, then moves the
# devices to that group. Note that even when using exact hostnames, there
# may be multiple matches found, and in that case all will be moved.
def move_devices(search_list, group_name, regex_hostname_search=False, cidr_search=False):
    # Get device IDs
    device_ids = get_device_ids(search_list=search_list, regex_hostname_search=regex_hostname_search, cidr_search=cidr_search)
    # Lookup to get Device Group ID
    group_id = get_group_id(group_name=group_name)
    # Execute the move
    result = add_devices_to_group(device_ids=device_ids, group_id=group_id)
    if result != None:
        return result + ' ' + group_name
    else:
        #something went wrong
        return none


# Accepts list of hostnames, removes any explicit/manual group assignment.
def move_devices_to_automatic_assignment(hostnames):
    #Get all devices from server
    devices = get_devices()

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

    # Convert to Pandas dataframes (to allow easy exports to Excel)
    windows_policies_df = pandas.DataFrame(windows_policies)
    mac_policies_df = pandas.DataFrame(mac_policies)
    ios_policies_df = pandas.DataFrame(ios_policies)
    android_policies_df = pandas.DataFrame(android_policies)
    chrome_policies_df = pandas.DataFrame(chrome_policies)
    network_agentless_policies_df = pandas.DataFrame(network_agentless_policies)

    # Get current timestamp and format for usage in exported filenames
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d_%H.%M')

    # Export data to disk

    folder_name = create_export_folder()

    file_name = f'windows_policies_{timestamp}.xlsx'
    windows_policies_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print('INFO:', len(windows_policies), 'policies written to', f'{folder_name}/{file_name}')

    file_name = f'mac_policies.xlsx_{timestamp}.xlsx'
    mac_policies_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print('INFO:', len(mac_policies), 'policies written to', f'{folder_name}/{file_name}')

    file_name = f'ios_policies.xlsx_{timestamp}.xlsx'
    ios_policies_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print('INFO:', len(ios_policies), 'policies written to', f'{folder_name}/{file_name}')

    file_name = f'android_policies_{timestamp}.xlsx'
    android_policies_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print('INFO:', len(android_policies), 'policies written to', f'{folder_name}/{file_name}')

    file_name = f'chrome_policies_{timestamp}.xlsx'
    chrome_policies_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print('INFO:', len(chrome_policies), 'policies written to', f'{folder_name}/{file_name}')

    file_name = f'network_agentless_policies_{timestamp}.xlsx'
    network_agentless_policies_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print('INFO:', len(network_agentless_policies), 'policies written to', f'{folder_name}/{file_name}')


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

    # Iterate through the policies
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
                request = requests.put(request_url, json=policy_data, headers=headers)
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


# Returns a list of all visible Tenants
def get_tenants():
    # Calculate headers and url
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/multitenancy/tenant/'

    # Get data from server
    response = requests.get(request_url, headers=headers)
    tenants = response.json()['tenants'] #convert to Python list, extract tenants

    return tenants


# Returns a list of all visible Devices
def get_devices():
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
        if response.status_code == 200: #this means successful query to server
            error_count = 0 #reset error_count to 0
            #print('INFO:', request_url, 'returned', response.status_code)
            response = response.json() #convert to Python list
            if 'last_id' in response:
                last_id = response['last_id'] #save returned last_id for reuse on next request
            else: #added this to handle issue where some server versions fail to return last_id on final batch of devices
                last_id = None
            if 'devices' in response:
                devices = response['devices'] #extract devices from response
                for device in devices: #iterate through the list of devices
                    collected_devices.append(device) #add to collected devices
        else:
            error_count += 1  #increment error counter
            print('WARN: Unexpected return code', response.status_code,
            'on request to\n', request_url, '\nwith headers\n', headers,
            '\nNew error_count is', error_count)
            time.sleep(10) #wait before trying request again

    # When while loop exists, we know we have collected all visible data

    # RETURN COLLECTED DATA
    return collected_devices


# Translates a list of device names, regex patterns, or CIDRs to a list of
# device IDs
def get_device_ids(search_list, regex_hostname_search=False, cidr_search=False):
    # GET ALL DEVICES
    devices = get_devices()

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
def get_group_id(group_name):

    # Get the groups from the server
    groups = get_groups()

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
def get_policies(include_policy_data=False, include_allow_deny_lists=False):
    # GET POLICIES (basic data only)

    # Calculate headers and URL
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/policies/'

    # Get data, convert to Python list
    response = requests.get(request_url, headers=headers)
    policies = response.json()

    # APPEND POLICY DATA (IF ENABLED)
    if include_policy_data:

        # Iterate through policy list
        for policy in policies:
            # Extract ID, calculate URL, and pull policy data from server
            policy_id = policy['id']
            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/data'
            response = requests.get(request_url, headers=headers)
            # Check response code (for some platforms, no policy data available)
            if response.status_code == 200:
                # Extract policy data from response and append it to policy
                policy_data = response.json()['data']
                policy.update(policy_data)

    # APPEND ALLOW-LIST AND DENY-LIST DATA (IF ENABLED)
    if include_allow_deny_lists:

        # Iterate through policy list
        for policy in policies:

            # Extract the policy id, which is used in subsequent requests
            policy_id = policy['id']

            # Each of the 6 code blocks below extract a specific type of allow-
            # or deny-list data from the server and append it to the policy
            # in policies (the collected data).

            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/allow-list/hashes'
            response = requests.get(request_url, headers=headers)
            if response.status_code == 200:
                allow_list_hashes = response.json()
                policy['allow_list_static_analysis_hashes'] = allow_list_hashes['items']

            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/allow-list/paths'
            response = requests.get(request_url, headers=headers)
            if response.status_code == 200:
                allow_list_paths = response.json()
                policy['allow_list_static_analysis_paths'] = allow_list_paths['items']

            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/allow-list/certificates'
            response = requests.get(request_url, headers=headers)
            if response.status_code == 200:
                allow_list_certificates = response.json()
                policy['allow_list_static_analysis_certificates'] = allow_list_certificates['items']

            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/allow-list/process_paths'
            response = requests.get(request_url, headers=headers)
            if response.status_code == 200:
                allow_list_process_paths = response.json()
                policy['allow_list_behavioral_analysis_process_paths'] = allow_list_process_paths['items']

            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/allow-list/scripts'
            response = requests.get(request_url, headers=headers)
            if response.status_code == 200:
                allow_list_scripts = response.json()
                policy['allow_list_script_control'] = allow_list_scripts['items']

            request_url = f'https://{fqdn}/api/v1/policies/{policy_id}/deny-list/hashes'
            response = requests.get(request_url, headers=headers)
            if response.status_code == 200:
                deny_list_hashes = response.json()
                policy['deny_list_static_analysis_hashes'] = deny_list_hashes['items']

    # RETURN THE COLLECTED DATA
    return policies


# Returns a list of all MSPs on the server
def get_msps():
    # Calculate headers and url
    headers = {'accept': 'application/json', 'Authorization': key}
    request_url = f'https://{fqdn}/api/v1/multitenancy/msp/'

    # Get data from server
    response = requests.get(request_url, headers=headers)
    msps = response.json()['msps']

    return msps


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
        return 'Success'
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
        return True
    else:
        return False


# Return a list of events matching specified search parameters and/or minimum
# event id. If neither are provided, all visible events are returned.
def get_events(search={}, minimum_event_id=0):

    #define HTTP headers for all requests in this method
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': key}

    #list to collect events
    collected_events = []

    #Note that the API method we are calling returns up to 50 events at a time,
    #and we know we have all events when we get last_id=None back in the response

    #loop until we have all the events
    while minimum_event_id != None:
        #calculate request url
        request_url = f'https://{fqdn}/api/v1/events/search/{str(minimum_event_id)}'
        #make request to server, store response
        response = requests.post(request_url, headers=headers, json=search)
        #check HTTP return code, and in case of error exit the method and return empty list
        print('INFO:', request_url, 'returned' , response.status_code)
        if response.status_code != 200:
            return []
        else:
            #store the returned last_id value
            minimum_event_id = response.json()['last_id']

            #if we got a none-null last_id back
            if minimum_event_id != None:
                #then extract the events
                events = response.json()['events']
                #append the event(s) from this response to collected_events
                for event in events:
                    collected_events.append(event)

    #return the list of collected events
    return collected_events

#Return a list of all events from 1 up to the provided max_event_id. This
#method is useful if you want to include Suspicous Events, which are not
#in scope for the API method used by the standard get_events method
def get_all_events(max_event_id, min_event_id=1):

    #define HTTP headers for all requests in this method
    headers = {'accept': 'application/json', 'Authorization': key}

    #list to collect events
    collected_events = []

    #loop until we have collected all events within specified range
    for event_id in range(min_event_id, max_event_id):
        request_url = f'https://{fqdn}/api/v1/events/{str(event_id)}'
        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            print('INFO:', request_url, 'returned', response.status_code)
            event = response.json()['event']
            collected_events.append(event)
        else:
            print('ERROR: Unexpected return code', response.status_code, 'on GET', request_url)

    return collected_events


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

#allows organization of exported data by server-specific folders
def create_export_folder():
    exported_data_folder_name = f'exported_data_from_{fqdn}'
    # Check if a folder already exists for data exports from this server
    if not os.path.exists(exported_data_folder_name):
        # ...If not, then create it
        os.makedirs(exported_data_folder_name)
    return exported_data_folder_name

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
# Example of how to copy Deep Instinct policies from one management server (or
# alternately a  single MSP within a multi-tenancy management server) to another

# KNOWN LIMITATIONS AND USAGE NOTES
# 1. If a policy by the same name already exists, it will be overwritten.
# 2. If a policy be the same name exists but it is for a different platform,
#    migration will be aborted. You need to fix this and run the script again.
# 3. If working with a multi-tenancy enabled server, you must provide API keys
#    for exactly 1 MSP. Anything else will throw an error and abort the script.
# 4. Only policy settings that are available to read and write via the
#    DI REST API are migrated. Any settings not visible via the API remain
#    unmodified on the destination server.
# 5. This script overwrites data but never deletes it. This means, for example,
#    that if allow lists or exclusions exist on the destination but not the
#    source, they will remain even after the migration script completes.

# USAGE
# 1. Save the latest version of both this file (policy_migration.py) and
#    the DI API Wrapper (deepinstinct3.py) to the same folder on disk.
# 2. Execute the script with this command:  python policy_migration.py
# 3. Answer the prompts.
# 4. Review results.

#define which platform(s) of policies to migrate
platforms_to_migrate = ['WINDOWS', 'MAC']

#define the type(s) of allow list, deny list, and exclusions to migrate
allow_deny_and_exclusion_list_types = ['allow-list/hashes', 'allow-list/paths', 'allow-list/certificates', 'allow-list/process_paths', 'allow-list/scripts', 'deny-list/hashes', 'exclusion-list/folder_path', 'exclusion-list/process_path']

#configuration parameters (optionally hardcode them here)
source_fqdn = 'FOO.customers.deepinstinctweb.com'
source_key = 'api_key_for_foo'
destination_fqdn = 'BAR.customers.deepinstinctweb.com'
destination_key = 'api_key_for_bar'

#prompt for configuration (unless hardcded values were provided above)
if source_fqdn == 'FOO.customers.deepinstinctweb.com':
    source_fqdn = input('FQDN of source DI Server? ')
if source_key == 'api_key_for_foo':
    source_key = input('API key for source server? ')
if destination_fqdn == 'BAR.customers.deepinstinctweb.com':
    destination_fqdn = input('FQDN of destination DI Server? ')
if destination_key == 'api_key_for_bar':
    destination_key = input('API key for source server (must be Full Access)? ')

#import REST API Wrapper - recommend to always use latest from https://github.com/pvz01/deepinstinct_rest_api_wrapper
import deepinstinct3 as di

#import additional libraries
import requests, sys, json

#get policies from source server
print('INFO: Getting policies from source server', source_fqdn)
di.fqdn = source_fqdn
di.key = source_key
source_server_policies = di.get_policies(include_policy_data=True, keep_data_encapsulated=True, include_allow_deny_lists=True)

#confirm that source server policy data is for a single MSP only (this script does not support multi-MSP policy migration)
source_server_msp_ids = []
for policy in source_server_policies:
    if policy['msp_id'] not in source_server_msp_ids:
        source_server_msp_ids.append(policy['msp_id'])
if len(source_server_msp_ids) != 1:
    print(f'ERROR: Unexpected data from source server {source_fqdn}! The policy list returned includes policies from {len(source_server_msp_ids)} unique MSPs. This must be 1. Please try again with a different API key.')
    sys.exit(0)

#get policies from destination server
print('INFO: Getting policies from destination server', destination_fqdn)
di.fqdn = destination_fqdn
di.key = destination_key
destination_server_policies = di.get_policies(include_policy_data=True, keep_data_encapsulated=True)

#confirm that destination server policy data is for a single MSP only (this script does not support multi-MSP policy migration)
destination_server_msp_ids = []
for policy in destination_server_policies:
    if policy['msp_id'] not in destination_server_msp_ids:
        destination_server_msp_ids.append(policy['msp_id'])
if len(destination_server_msp_ids) != 1:
    print(f'ERROR: Unexpected data from destination server {source_fqdn}! The policy list returned includes policies from {len(destination_server_msp_ids)} unique MSPs. This must be 1. Please try again with a different API key.')
    sys.exit(0)

#safety check for cross-platform policy name collission (breaks future logic)
print('INFO: Checking for cross-platform policy name collission')
for source_policy in source_server_policies:
    for destination_policy in destination_server_policies:
        if source_policy['name'] == destination_policy == ['name']:
            if source_policy['os'] != destination_policy['os']:
                print('ERROR: Unable to proceed with migration because policy', source_policy['name'], 'is a', source_policy['os'], 'policy on the source server and a policy with the same name is a', destination_policy['os'], 'policy on the destination server.')
                sys.exit(0)

#build a list of policy names from destination server
destination_server_policy_names = []
for policy in destination_server_policies:
    destination_server_policy_names.append(policy['name'])

#build dictionary of default policy IDs on destination server
print('INFO: Building dictionary of default policy IDs by platform on', destination_fqdn)
destination_default_policy_ids = {}
for policy in destination_server_policies:
    if policy['is_default_policy']:
        destination_default_policy_ids[policy['os']] = policy['id']

#build list of policies to migrate
policies_to_migrate = []
for source_server_policy in source_server_policies:
    if source_server_policy['os'] in platforms_to_migrate:
        policies_to_migrate.append(source_server_policy)

#Confirm with user
print('INFO: Prep work is done. Ready to migrate data from', source_fqdn, 'to', destination_fqdn)
print('The following', len(policies_to_migrate), 'policies will be migrated:')
print(json.dumps(policies_to_migrate, indent=4))
print()
user_prompt_text = f'Do you want to proceed with migrating the {str(len(policies_to_migrate))} policies detailed above [YES | NO] ?  '
user_response = input(user_prompt_text)
if user_response.lower() != 'yes':
    print('WARNING: Terminating script based on user response', user_response)
    sys.exit(0)
else:
    print('INFO: Proceeding with migration based on user response', user_response)

    #define a counter used for console output during policy migration
    counter = 1

    #Migrate the policies
    for policy in policies_to_migrate:

        #first step is to create the base policy, which we'll base on the platform-specific default policy
        print('\nINFO: Beginning migration of policy', counter, 'of', len(policies_to_migrate), ':', policy['os'], 'policy', policy['id'], policy['name'])
        if policy['name'] in destination_server_policy_names:
            for destination_server_policy in destination_server_policies:
                if policy['name'] == destination_server_policy['name']:
                    new_policy = destination_server_policy
                    print('      Reusing existing policy on destination server:', new_policy['id'], new_policy['name'], new_policy['os'])
        else:
            new_policy = di.create_policy(policy['name'], destination_default_policy_ids[policy['os']], quiet_mode=True)
            print('      Newly created policy on destination server:', new_policy['id'], new_policy['name'], new_policy['os'])

        #next step is to overwrite the policy data on the newly-create policy with data from old server
        print('      Overwriting policy data on new policy', new_policy['id'], 'with data collected from old policy', policy['id'])
        new_policy_id = new_policy['id']
        request_url = f'https://{di.fqdn}/api/v1/policies/{new_policy_id}/data'
        headers = {'accept': 'application/json', 'Authorization': di.key}
        payload = {'data': policy['data']}
        response = requests.put(request_url, json=payload, headers=headers)
        if response.status_code == 204:
            print('      Successfully overwrote policy data on new policy', new_policy['id'])
        else:
            print('ERROR: Unexpected response', response.status_code, 'on PUT to', request_url)
            sys.exit(0)

        #last step is to migrate the associated allow list, deny list, and exclusion lists for the policy
        print('      Copying any existing allow list, deny list, and exclusion lists from policy', policy['id'], 'to policy', new_policy['id'])
        headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': di.key}
        for list_type in allow_deny_and_exclusion_list_types:
            if list_type in policy['allow_deny_and_exclusion_lists']:
                if len(policy['allow_deny_and_exclusion_lists'][list_type]['items']) > 0:
                    payload = policy['allow_deny_and_exclusion_lists'][list_type]
                    request_url = f'https://{di.fqdn}/api/v1/policies/{new_policy_id}/{list_type}'
                    response = requests.post(request_url, headers=headers, json=payload)
                    if response.status_code == 204:
                        print('      Successfully copied', len( policy['allow_deny_and_exclusion_lists'][list_type]['items'] ), 'entries of type', list_type)
                    elif response.status_code == 404:
                        print('WARNING: Response', response.status_code, 'on POST to', request_url, '. This indicates data of this type existed on the source server but was not migrated to the destination server due to no available API method on the destination.')
                    else:
                        print('ERROR: Unexpected response', response.status_code, 'on POST to', request_url, 'with payload', payload)
                        sys.exit(0)
        print('INFO: Done with migration of policy', counter, 'of', len(policies_to_migrate), ':', policy['os'], 'policy', policy['id'], policy['name'])
        counter += 1

    print('\nDone migrating', len(policies_to_migrate), 'policies from', source_fqdn, 'to', destination_fqdn)

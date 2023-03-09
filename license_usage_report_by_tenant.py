# Example of how to generate a usage/billing report on a multi-tenancy server.
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

import pandas, datetime, deepinstinct30 as di, sys

# Optional hardcoded config - if not provided, you'll be prompted at runtime
di.fqdn = 'SERVER-NAME.customers.deepinstinctweb.com'
di.key = 'API-KEY'
include_policy_mode_counts = ''

# Validate config and prompt if not provided above
while di.fqdn in ('SERVER-NAME.customers.deepinstinctweb.com', ''):
    di.fqdn = input('FQDN of [multi-tenancy] DI Server? [foo.bar.deepinstinctweb.com] ')
while di.key in ('API-KEY', ''):
    di.key = input('API Key with visibility into all MSPs and Tenants on the server? ')
while include_policy_mode_counts not in (True, False):
    input_response = input('Include prevention/detection mode counts? [Yes | No] ')
    if input_response.lower() == 'yes':
        include_policy_mode_counts = True
    elif input_response.lower() == 'no':
        include_policy_mode_counts = False
    else:
        print('ERROR: Invalid response:', input_response)
        sys.exit(0)

#get tenant data from server
print('INFO: Getting Tenant data from server')
tenants = di.get_tenants()

#confirm that we got valid data back; if not, abort script
if len(tenants) == 0:
    print('ERROR: No Tenants returned. Check that server is multi-tenancy enabled and that your API key has the appropriate permissions.')
    sys.exit(0)

#get msp data from server
print('INFO: Getting MSP data from server')
msps = di.get_msps()

# get device data from server
print('INFO: Getting Device data from server')
devices = di.get_devices(include_deactivated=False)

# add msp_name to tenant data
print('INFO: Adding MSP names to Tenant data')
for tenant in tenants:
    for msp in msps:
        if tenant['msp_id'] == msp['id']:
            tenant['msp_name'] = msp['name']

# If option to include policy mode counts is enabled, get policy details,
# then parse policies to calculate mode, then add that data to devices
if include_policy_mode_counts:
    print('INFO: Getting policy data from server')
    policies = di.get_policies(include_policy_data=True)

    print('INFO: Parsing policy data to determine policy mode')

    for policy in policies:

        policy['prevention_mode'] = False

        if policy['os'] == 'WINDOWS':
            if policy['prevention_level'] in ('LOW', 'MEDIUM', 'HIGH'):
                if policy['ransomware_behavior'] == 'PREVENT':
                    if policy['remote_code_injection'] == 'PREVENT':
                        if policy['arbitrary_shellcode_execution'] == 'PREVENT':
                            policy['prevention_mode'] = True

        elif 'prevention_level' in policy.keys():
            if policy['prevention_level'] in ('LOW', 'MEDIUM', 'HIGH'):
                policy['prevention_mode'] = True

    print('INFO: Adding policy mode to device data')
    for device in devices:
        for policy in policies:
            if policy['id'] == device['policy_id']:
                device['prevention_mode'] = policy['prevention_mode']

# Calculate license usage for each tenant (plus prevention/detection data, if enabled in config)
if include_policy_mode_counts:
    print('INFO: Parsing device data to calculate licenses used plus prevention/detection counts for each tenant')
else:
    print('INFO: Parsing device data to calculate licenses used for each tenant')
for tenant in tenants:
    tenant['licenses_used'] = 0
    if include_policy_mode_counts:
        tenant['devices_in_prevention_mode'] = 0
        tenant['devices_in_detection_mode'] = 0
for device in devices:
    # Check if the device has an activated license (if not skip it)
    if device['license_status'] == 'ACTIVATED':
        # If yes, then find the Tenant that this device belongs to
        for tenant in tenants:
            if tenant['id'] == device['tenant_id']:
                # ...and increment the licenses_used counter in the matching tenant by 1
                tenant['licenses_used'] += 1
                # If enabled, also increment the prevention/detection counter
                if include_policy_mode_counts:
                    if device['prevention_mode']:
                        tenant['devices_in_prevention_mode'] += 1
                    else:
                        tenant['devices_in_detection_mode'] += 1

# Calculate percent_of_licenses_used for reach tenant and add results to tenants data
print('INFO: Calculating percentage of licenses used for each tenant')
for tenant in tenants:
    if tenant['license_limit'] == 0:  #avoids a divisiion by zero error for tenants with no assigned licenses
        tenant['percent_of_licenses_used'] = 0
    else:
        tenant['percent_of_licenses_used'] = (tenant['licenses_used'] / tenant['license_limit'])

# If enabled in config, calculate percentage of devices in prevention mode and add to tenant data
if include_policy_mode_counts:
    print('INFO: Calculating percentage of devices in prevention mode for each tenant')
    for tenant in tenants:
        if tenant['licenses_used'] == 0:  #avoid division by zero for empty tenants
            tenant['percent_of_devices_in_prevention'] = 0
        else:
            tenant['percent_of_devices_in_prevention'] = (tenant['devices_in_prevention_mode'] / tenant['licenses_used'])

# Convert the data to a Pandas data frame for easier manipulation and export
print('INFO: Preparing data for export')
tenants_df = pandas.DataFrame(tenants)

# Sort the data frame alphabetically by msp name and then by tenant name
print('INFO: Sorting data for export')
tenants_df.sort_values(by=['msp_name', 'name'], inplace=True)

# Export the sorted data frame to disk in Excel format
print('INFO: Calculating export folder name and file name')
folder_name = di.create_export_folder()
file_name = f'license_usage_report_by_tenant_{di.fqdn}_{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H.%M")}_UTC.xlsx'
print('INFO: Exporting data to disk')
if include_policy_mode_counts:
    tenants_df.to_excel(f'{folder_name}/{file_name}', index=False, columns=['msp_name', 'name', 'licenses_used', 'license_limit', 'percent_of_licenses_used', 'devices_in_prevention_mode', 'devices_in_detection_mode', 'percent_of_devices_in_prevention'])
else:
    tenants_df.to_excel(f'{folder_name}/{file_name}', index=False, columns=['msp_name', 'name', 'licenses_used', 'license_limit', 'percent_of_licenses_used'])
print('INFO: Data was exported to disk as', f'{folder_name}/{file_name}')

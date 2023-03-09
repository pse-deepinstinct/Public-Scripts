# Older example of how to compare policy settings to a set of "desired"
# settings and write them to a text file. Recommend to consider using
# the newer 'policy_and_user_audit.py' script instead, since it is MUCH more
# feature complete and produces a more flexible output.
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
import deepinstinct3 as di, datetime

def do_warranty_compliance_check(fqdn, key, exclude_empty_policies):
    di.fqdn = fqdn
    di.key = key

    #Get data from server
    print('INFO: Getting policy data from server')
    policies = di.get_policies(include_policy_data=True)
    print('INFO: Getting device data from server')
    devices = di.get_devices(include_deactivated=False)

    # Calculate device_count for each policy (how many active devices in policy)
    # Add device_countfield with initial value zero
    print('INFO: Calculating device count for each policy')
    for policy in policies:
        policy['device_count'] = 0
    # Iterate through devices and policies, incrementing device_count appropriately
    for device in devices:
        for policy in policies:
            if policy['id'] == device['policy_id']:
                policy['device_count'] +=1

    if exclude_empty_policies:
        print('INFO: Narrowing policy list to include only those which contain 1 or more activated devices')
        non_empty_policies = []
        for policy in policies:
            if policy['device_count'] > 0:
                non_empty_policies.append(policy)
        empty_policy_count = len(policies) - len(non_empty_policies)
        policies = non_empty_policies
    else:
        print('INFO: exclude_empty_policies is disabled, therefore proceeding with analysis on all policies')

    #Extract Windows policies
    print('INFO: Extracting Windows policies to new list windows_policies')
    windows_policies = []
    for policy in policies:
        if policy['os'] == 'WINDOWS':
            windows_policies.append(policy)

    #Iterate through Windows policies, determine compliance or lack thereof, and assign to appropriate list

    print('INFO: Analyzing policies for compliance')

    compliant_windows_policies = []
    noncompliant_windows_policies = []

    for policy in windows_policies:

        policy['compliant'] = True  #initially assume compliant; will change to false if violation(s) identified
        policy['compliance_violations'] = {}  #define dictionary to store details of violation(s) if any

        if policy['prevention_level'] not in ['HIGH', 'MEDIUM', 'LOW']:
            policy['compliant'] = False
            policy['compliance_violations']['prevention_level'] = policy['prevention_level']

        if policy['remote_code_injection'] != 'PREVENT':
            policy['compliant'] = False
            policy['compliance_violations']['remote_code_injection'] = policy['remote_code_injection']

        if policy['arbitrary_shellcode_execution'] != 'PREVENT':
            policy['compliant'] = False
            policy['compliance_violations']['arbitrary_shellcode_execution'] = policy['arbitrary_shellcode_execution']

        if policy['ransomware_behavior'] != 'PREVENT':
            policy['compliant'] = False
            policy['compliance_violations']['ransomware_behavior'] = policy['ransomware_behavior']

        #TODO: Add logic to check the following atttributes of the Windows policy:
        #   1. D-Cloud Services (compliance requires that this be enabled)
        #   2. Malicious PowerShell Prevention (compliance requires that this be in Prevention)
        #Both of above require that product make these fields visible via the REST API. Submitted
        #as FR-166 and FR-167 on 2021-07-06

        if policy['compliant'] == True:
            compliant_windows_policies.append(policy)
        else:
            noncompliant_windows_policies.append(policy)

    #Calculate how many devices are in compliant versus non-compliance policies

    print('INFO: Counting sum of devices in policies in each category')

    device_count_compliant_windows_policies = 0
    for policy in compliant_windows_policies:
        device_count_compliant_windows_policies += policy['device_count']

    device_count_noncompliant_windows_policies = 0
    for policy in noncompliant_windows_policies:
        device_count_noncompliant_windows_policies += policy['device_count']


    #Write results to disk

    print('INFO: Calculating file and folder names for export')
    folder_name = di.create_export_folder()
    file_name = f'warranty_compliance_audit_{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H.%M")}_UTC.txt'

    print('INFO: Opening file for writing data to to disk')
    output = open(f'{folder_name}\{file_name}', 'a')

    print('INFO: Writing data to disk')

    output.writelines(['--------\nDeep Instinct Ransomware Warranty Compliance Check\n', di.fqdn, '\n', datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H.%M"), ' UTC\n--------\n\n'])

    if exclude_empty_policies:
        if empty_policy_count > 0:
            output.writelines(['NOTE: Data below excludes ', str(empty_policy_count), ' policies containing 0 activated devices.\n\n'])

    output.writelines([str(device_count_compliant_windows_policies), ' devices are in a compliant Windows policy.\n'])
    output.writelines([str(device_count_noncompliant_windows_policies), ' devices are in a non-compliant Windows policy.\n'])
    output.writelines(['\n', str(len(compliant_windows_policies)), ' Windows policies are compliant:\n\n'])
    output.writelines(['msp_id\tmsp_name\tpolicy_id\tpolicy_name\tdevice_count\tcompliance_violations\n'])
    for policy in compliant_windows_policies:
        output.writelines([str(policy['msp_id']), '\t', policy['msp_name'], '\t', str(policy['id']), '\t', policy['name'], '\t', str(policy['device_count']), '\t', str(policy['compliance_violations']), '\n'])
    output.writelines(['\n', str(len(noncompliant_windows_policies)), ' Windows policies are non-compliant:\n\n'])
    output.writelines(['msp_id\tmsp_name\tpolicy_id\tpolicy_name\tdevice_count\tcompliance_violations\n'])
    for policy in noncompliant_windows_policies:
        output.writelines([str(policy['msp_id']), '\t', policy['msp_name'], '\t', str(policy['id']), '\t', policy['name'], '\t', str(policy['device_count']), '\t', str(policy['compliance_violations']), '\n'])

    print('INFO: Closing file for writing data to to disk')
    output.close()

    print('INFO: Done. Results written to', f'{folder_name}\{file_name}')

def main():
    fqdn = input('FQDN of DI Server? [foo.bar.deepinstinctweb.com] ')
    key = input('API Key? ')
    exclude_empty_policies = False
    exclude_empty_policies_question_response = input('Ignore empty policies? [Yes | No] ')
    if exclude_empty_policies_question_response.lower() == 'yes':
        exclude_empty_policies = True
    do_warranty_compliance_check(fqdn=fqdn, key=key, exclude_empty_policies=exclude_empty_policies)


if __name__ == "__main__":
    main()

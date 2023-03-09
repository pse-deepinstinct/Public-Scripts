# Example of how to read data from Excel files and write it to the server using
# REST API methods. In this case, we are reading an Excel document for one or
# more exclusions or allow lists of one or more types. I recommend to reference
# exclusions_example_*.xlsx as example of the proper format and to then use
# these files as your template.
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
import pandas
import time


def main():

    #prompt for config parameters

    fqdn = input('Enter FQDN of DI Server, or press enter to accept the default [di-service.customers.deepinstinctweb.com]: ')
    if fqdn == '':
        fqdn = 'di-service.customers.deepinstinctweb.com'

    key = input('Enter API Key for DI Server: ')

    print_readme()

    file_name = input('Enter name of file containing the exclusions to import, or press enter to accept the default [exclusions.xlsx]: ')
    if file_name == '':
        file_name = 'exclusions.xlsx'

    #run the import
    return run_exclusion_import(fqdn=fqdn, key=key, file_name=file_name)


def run_exclusion_import(fqdn, key, file_name):

    start_time = time.perf_counter()

    di.fqdn = fqdn
    di.key = key

    #read exclusions from files on disk as Pandas dataframes
    process_exclusions_dataframe = pandas.read_excel(file_name, sheet_name='Process')
    folder_exclusions_dataframe = pandas.read_excel(file_name, sheet_name='Folder')
    behavioral_allow_lists_dataframe = pandas.read_excel(file_name, sheet_name='Behavioral')
    script_allow_lists_dataframe = pandas.read_excel(file_name, sheet_name='Script')

    #replace any null values with empty string to avoid subsequent errors
    process_exclusions_dataframe.fillna('', inplace=True)
    folder_exclusions_dataframe.fillna('', inplace=True)
    behavioral_allow_lists_dataframe.fillna('', inplace=True)
    script_allow_lists_dataframe.fillna('', inplace=True)

    #convert Pandas dataframes to Python dictionaries
    process_exclusions = process_exclusions_dataframe.to_dict('records')
    folder_exclusions = folder_exclusions_dataframe.to_dict('records')
    behavioral_allow_lists = behavioral_allow_lists_dataframe.to_dict('records')
    script_allow_lists = script_allow_lists_dataframe.to_dict('records')

    #convert fields expected to contain comma-separated lists from strings to lists
    for item in process_exclusions:
        item['Policies'] = item['Policies'].split(", ")
    for item in folder_exclusions:
        item['Policies'] = item['Policies'].split(", ")
    for item in behavioral_allow_lists:
        item['Policies'] = item['Policies'].split(", ")
        item['Behaviors'] = item['Behaviors'].split(", ")
    for item in script_allow_lists:
        item['Policies'] = item['Policies'].split(", ")

    #get policy list, then filter it to get a list of just Windows policies
    all_policies = di.get_policies()
    windows_policies = []
    for policy in all_policies:
        if policy['os'] == 'WINDOWS':
            windows_policies.append(policy)

    #iterate through each of the Windows policies
    for policy in windows_policies:

        print('INFO: Beginning processing of policy', policy['id'], policy['name'])


        #PROCESS EXCLUSIONS

        #create a list to store process exclusions that apply to this policy
        process_exclusions_this_policy = []

        #iterate though the imported process exclusion list
        for exclusion in process_exclusions:
            #check if the exclusion applies to all policies
            if exclusion['Policies'] == ['All']:
                process_exclusions_this_policy.append(exclusion)
            #check if the exclusion applies to this specific policy
            elif policy['name'] in exclusion['Policies']:
                process_exclusions_this_policy.append(exclusion)

        #if we found some exclusions applicable to this policy, create them
        if len(process_exclusions_this_policy) > 0:
            print('INFO: Adding', len(process_exclusions_this_policy), 'process exclusions to policy', policy['id'], policy['name'])
            for exclusion in process_exclusions_this_policy:
                di.add_process_exclusion(exclusion=exclusion['Process'], comment=exclusion['Comment'], policy_id=policy['id'])


        #FOLDER EXCLUSIONS

        #create a list to store folder exclusions that apply to this policy
        folder_exclusions_this_policy = []

        #iterate though the imported folder exclusion list
        for exclusion in folder_exclusions:
            #check if the exclusion applies to all policies
            if exclusion['Policies'] == ['All']:
                folder_exclusions_this_policy.append(exclusion)
            #check if the exclusion applies to this specific policy
            elif policy['name'] in exclusion['Policies']:
                folder_exclusions_this_policy.append(exclusion)

        #if we found some exclusions applicable to this policy, create them
        if len(folder_exclusions_this_policy) > 0:
            print('INFO: Adding', len(folder_exclusions_this_policy), 'folder exclusions to policy', policy['id'], policy['name'])
            for exclusion in folder_exclusions_this_policy:
                di.add_folder_exclusion(exclusion=exclusion['Folder'], comment=exclusion['Comment'], policy_id=policy['id'])


        #BEHAVIORAL ANALYSIS ALLOW LIST

        #create a list to store entries that apply to this policy
        behavioral_this_policy = []

        #iterate though the imported folder exclusion list
        for exclusion in behavioral_allow_lists:
            #check if the exclusion applies to all policies
            if exclusion['Policies'] == ['All']:
                behavioral_this_policy.append(exclusion)
            #check if the exclusion applies to this specific policy
            elif policy['name'] in exclusion['Policies']:
                behavioral_this_policy.append(exclusion)

        #if we found some exclusions applicable to this policy, create them
        if len(behavioral_this_policy) > 0:
            print('INFO: Adding', len(behavioral_this_policy), 'behavioral allow lists to policy', policy['id'], policy['name'])
            for exclusion in behavioral_this_policy:
                di.add_behavioral_allow_lists(process_list=[exclusion['Process']], behavior_name_list=exclusion['Behaviors'], comment=exclusion['Comment'], policy_id=policy['id'])


        #SCRIPT ALLOW LIST

        #create a list to store folder exclusions that apply to this policy
        script_this_policy = []

        #iterate though the imported folder exclusion list
        for exclusion in script_allow_lists:
            #check if the exclusion applies to all policies
            if exclusion['Policies'] == ['All']:
                script_this_policy.append(exclusion)
            #check if the exclusion applies to this specific policy
            elif policy['name'] in exclusion['Policies']:
                script_this_policy.append(exclusion)

        #if we found some exclusions applicable to this policy, create them
        if len(script_this_policy) > 0:
            print('INFO: Adding', len(script_this_policy), 'script allow lists to policy', policy['id'], policy['name'])
            for exclusion in script_this_policy:
                di.add_script_path_allow_list(path=exclusion['Path'], comment=exclusion['Comment'], policy_id=policy['id'])


        print('INFO: Done with policy', policy['id'], policy['name'])

    runtime_in_seconds = time.perf_counter() - start_time
    print('Runtime was', runtime_in_seconds, 'seconds.')

def print_readme():
    print("""
-- USAGE NOTES ---

This script accepts a single input file and has the ability to create up to
three types of exclusions in bulk:
1. Static Analysis Process Exclusions
2. Static Analysis Folder Exclusions
3. Behavioral Analysis Allow Lists
4. Script Path Allow Lists

The input file must be an OOXML spreadsheet (.xlsx file) and contain at minimum
four sheets (tabs). Those sheets must be named:
1. Process
2. Folder
3. Behavioral
4. Script
Sheet order is irrelevant. Additional sheets, if present, will be ignored.
Sheet names are cASe SeNSITIVe. All sheets and their required column names
detailed below must always be present, even if they contain no entries to
import.

The 'Process' sheet must contain the following columns. Column names are
cASE seNSITive. Column order is irrelevant. Additional columns will be ignored.
1. Process
2. Policies
3. Comment

The 'Folder' sheet must contain the following columns. Column names are
cASE seNSITive. Column order is irrelevant. Additional columns will be ignored.
1. Folder
2. Policies
3. Comment

The 'Behavioral' sheet must contain the following columns. Column names are
cASE seNSITive. Column order is irrelevant. Additional columns will be ignored.
1. Process
2. Behaviors
3. Policies
4. Comment

The 'Script' sheet must contain the following columns. Column names are
cASE seNSITive. Column order is irrelevant. Additional columns will be ignored.
1. Path
2. Policies
3. Comment

For all 3 sheets, the 'Policies' column must contain one of the following:
A. The word All
B. The name of one policy
C. A list of policies delimited by <comma><space>. Example: Policy 1, Policy 2
Note: All of the above are cASE seNSITive

For the 'Behavioral' sheet, the 'Behaviors' column  must contain one of the
following:
A. The word All
B. The name of one specific behavior
C. A list of behaviors delimited by <comma><space>. Example: Behavior1, Behavior2

For the 'Behavioral' sheet, the accepted values to includes in the 'Behaviors'
column are:
1. RANSOMWARE_FILE_ENCRYPTION
2. REMOTE_CODE_INJECTION_EXECUTION
3. KNOWN_SHELLCODE_PAYLOADS
4. ARBITRARY_SHELLCODE_EXECUTION
5. REFLECTIVE_DLL
6. REFLECTIVE_DOTNET
7. AMSI_BYPASS
8. DIRECT_SYSTEMCALLS
9. CREDENTIALS_DUMP
Note: All of the above are cASE seNSITive

Reference exclusions_example_*.xlsx files for examples of the proper format.

""")


if __name__ == "__main__":
    main()

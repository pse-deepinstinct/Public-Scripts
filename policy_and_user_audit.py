# This example script audits all Windows policies against a defined set of
# desired settings (Best Practices or otherwise) and produces a Excel document
# which includes all settings from all policies and color-codes them to indicate
# compliance versis non-compliance with the desired settings. To do so it
# requres both a REST API key and a username/password for interactive login (the
# latter is used to collect data not currently exposed in the REST API).
# Additionally, it includes a list of policies and groups.
# It optionally includes an audit of adminitrator accounts (interactive users)
# including mark-up of days since last login to identify stale accounts.
# When using all features, you will two API keys plus a username/password pair.
# This script makes extensive usage of Pandas, including logic to auto resize
# columns, to apply conditional formatting to cells, and more.
#
# A common use case of a script such as this is to automate "Health Check"
# type activities, whether at an MSP level or for an entire server.
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
import datetime, pandas, json, re
import requests
import collections
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)


def main():

    include_user_account_list, account_management_api_key = prompt_user_for_config()

    policies_internal_api = get_windows_policies_internal_api()

    print('\nGathering Windows policy data using external/public API\n')
    policies_external_api = di.get_policies(os_list = ['WINDOWS'], include_policy_data=True,)

    print('\nMerging the policy data from the two sources\n')
    policies = merge_policies(policies_external_api, policies_internal_api)

    print('\nChecking if server is multi-tenancy')
    mt = di.is_server_multitenancy_enabled()
    print(mt)

    if mt:
        print('\nGetting list of MSPs')
        msps = di.get_msps()
    else:
        msps = []

    print('\nChecking if we have policy data from >1 MSP')
    multi_msp = data_from_more_than_one_msp(policies)
    print(multi_msp)

    print('\nBuilding results')
    results = build_results(policies, multi_msp)

    print('\nAdding group count information to results\n')
    results, groups = add_group_counts(results)

    print('\nAdding device count information to results\n')
    results, devices = add_device_counts(results)

    print('\nConverting results to DataFrame')
    results_df = pandas.DataFrame(results)

    print('\nSorting results')
    if multi_msp:
        results_df.sort_values(by=['MSP Name','Name'], inplace=True)
    else:
        results_df.sort_values(by=['Name'], inplace=True)

    print('\nModifying column order')
    if multi_msp:
        results_df = move_df_column_to_position(results_df, 'Group Count', 4)
        results_df = move_df_column_to_position(results_df, 'Device Count', 5)
    else:
        results_df = move_df_column_to_position(results_df, 'Group Count', 2)
        results_df = move_df_column_to_position(results_df, 'Device Count', 3)

    print('\nComparing Data to Best Practices and applying conditional formatting to DataFrame')
    results_df_stylized = evaluate_and_apply_conditional_formatting(results_df)

    print('\nBuilding Group List (used for Configuration Document at project closure)')
    groups_df = generate_group_list(groups, devices, policies, mt)
    if 'MSP Name' in groups_df.columns and not multi_msp:
        groups_df.pop('MSP Name')

    print('\nBuilding Administrator Accounts list (used for Configuration Document at project closure)')
    users_df, users_df_styliyzed = get_user_list(include_user_account_list, account_management_api_key, mt, msps)

    print('\nExporting data to disk\n')
    folder_name = di.create_export_folder()
    file_name = calculate_export_file_name(policies, mt, multi_msp)
    export_results(results_df, results_df_stylized, f'{folder_name}/{file_name}', groups_df, include_user_account_list, users_df, users_df_styliyzed, mt, multi_msp)


def get_user_list(include_user_account_list, account_management_api_key, mt, msps):

    if not include_user_account_list:
        print('WARNING: Skipping export of user list due to no provided account_management_api_key.')
        users_df = pandas.DataFrame([])

    else:
        di.key = account_management_api_key
        users = di.get_users()

        if mt:
            for user in users:
                if 'msp_id' in user.keys():
                    for msp in msps:
                        if msp['id'] == user['msp_id']:
                            user['MSP ID'] = user['msp_id']
                            user['MSP Name'] = msp['name']
                            break

        users_df = pandas.DataFrame(users)

        users_df['last_login'] = pandas.to_datetime(users_df.last_login, format='%Y-%m-%d %H:%M:%S').dt.strftime('%Y-%m-%d')
        users_df['role'] = users_df['role'].str.title()
        users_df['role'] = users_df['role'].str.replace('_', ' ')
        users_df['last_login_days_ago'] = (pandas.to_datetime(pandas.to_datetime('now').strftime('%Y-%m-%d')) - pandas.to_datetime(users_df['last_login'])).dt.days
        users_df = users_df.fillna('')

        #remove unwanted fields
        users_df.pop('auth_type')
        users_df.pop('id')
        users_df.pop('email')
        if mt:
            users_df.pop('msp_id')

        #re-arrange columns
        users_df = move_df_column_to_position(users_df, 'role', 0)
        users_df = move_df_column_to_position(users_df, 'username', 1)
        users_df = move_df_column_to_position(users_df, 'first_name', 2)
        users_df = move_df_column_to_position(users_df, 'last_name', 3)
        users_df = move_df_column_to_position(users_df, 'last_login', 4)
        users_df = move_df_column_to_position(users_df, 'last_login_days_ago', 5)

        #rename columns to be more human friendly
        users_df.rename(columns={'role': 'Role', 'username': 'User Name', 'first_name': 'First Name', 'last_name': 'Last Name', 'last_login': 'Last Login', 'last_login_days_ago': 'Days Ago'}, inplace=True)

        #sort data
        users_df.sort_values(by=['Role', 'User Name'], inplace=True)

    users_df_styliyzed = users_df.style.applymap(highlight_days_ago, subset=['Days Ago'])

    return users_df, users_df_styliyzed


def highlight_days_ago(actual):

    if actual == '':
        #never logged in
        return 'background-color: {}'.format('#FFB3BA') #light red

    elif actual >= 60:
        #last login 2+ months ago
        return 'background-color: {}'.format('#FFB3BA') #light red

    elif actual >= 30:
        #last login 1+ month ago
        return 'background-color: {}'.format('#FFFF8F') #light yellow


def generate_group_list(groups, devices, policies, mt):
    group_table = []
    if mt:
        msps = di.get_msps()
    for group in groups:
        if group['os'] == 'WINDOWS':
            group['devices'] = 0
            for device in devices:
                if group['id'] == device['group_id']:
                    group['devices'] += 1
            for policy in policies:
                if group['policy_id'] == policy['id']:
                    group['policy_name'] = policy ['name']
            result = {}
            if mt:
                for msp in msps:
                    if group['msp_id'] == msp['id']:
                        group['msp_name'] = msp['name']
                result['MSP Name'] =  group['msp_name']
            result['Group Name'] = group['name']
            result['Policy Name'] = group['policy_name']
            result['Device Count'] = group['devices']
            group_table.append(result)
    groups_df = pandas.DataFrame(group_table)
    return groups_df


def prompt_user_for_config():
    di.fqdn = input('FQDN: ')
    if di.fqdn == '':
        di.fqdn = 'di-service.customers.deepinstinctweb.com'
    di.key = input('API Key 1 of 2- Full Access or Read Only): ')
    account_management_api_key = input('API Key 2 of 2 - Account Management (to skip export of Administrator Account list, leave blank): ')
    if len(account_management_api_key) > 0:
        return True, account_management_api_key
    else:
        return False, account_management_api_key


def data_from_more_than_one_msp(policies):
    policy_msp_ids = []
    for policy in policies:
        if policy['msp_id'] not in policy_msp_ids:
            policy_msp_ids.append(policy['msp_id'])
    if len(policy_msp_ids) > 1:
        return True
    else:
        return False


def highlight_cells(actual, expected):
    if str(expected).lower() == str(actual).lower():
        color = '#BAFFC9' #light green
    else:
        color = '#FFB3BA' #light red
    return 'background-color: {}'.format(color)


def evaluate_and_apply_conditional_formatting(df):

    #define lists of fields that are expected to have particular values
    should_be_prevent = ['Known PUA', 'Ransomware Behavior', 'Arbitrary Shellcode', 'Remote Code Injection',
                        'Reflective DLL Injection', '.Net Reflection', 'AMSI Bypass', 'Credential Dumping', 'Known Payload Executionn',
                        'HTML Applications', 'ActiveScript Execution - If allowed by Windows, action when non-allow-listed script runs',
                        'Suspicious Script Execution', 'Malicious PowerShell Command Execution', 'Malicious JavaScript Execution',
                        'Dual use tools']
    should_be_allow = ['Suspicious PowerShell Command Execution', 'PowerShell execution', 'Embedded DDE in Office files']
    should_be_true = ['Upgrades Enabled', 'Enable D-Cloud services', 'Scan Files Accessed from Network', 'In-Memory Protection']
    should_be_moderate = ['PE Detection Threshold', 'PE Prevention Threshold']
    should_be_use_d_brain = ['Macro Execution']
    should_be_default_windows_action = ['ActiveScript Execution - When ActiveScripts are executed']

    #for each of the lists above, check actual versus expected and apply conditional formatting
    s = df.style.applymap(highlight_cells, expected='prevent', subset=should_be_prevent)
    s = s.applymap(highlight_cells, expected='allow', subset=should_be_allow)
    s = s.applymap(highlight_cells, expected='true', subset=should_be_true)
    s = s.applymap(highlight_cells, expected='moderate', subset=should_be_moderate)
    s = s.applymap(highlight_cells, expected='use_d_brain', subset=should_be_use_d_brain)
    s = s.applymap(highlight_cells, expected='default windows action', subset=should_be_default_windows_action)


    return s


def build_results(policies, multi_msp):
    results = []
    for policy in policies:
        result = {}
        if multi_msp:
            result['MSP ID'] = policy['msp_id']
            result['MSP Name'] = policy['msp_name']
        result['ID'] = policy['id']
        result['Name'] = policy['name']
        result['Upgrades Enabled'] = str(policy['automatic_upgrade']).capitalize()
        result['Enable D-Cloud services'] = str(policy['enable_dcloud']).capitalize()
        result['Scan Files Accessed from Network'] = str(policy['scan_network_drives']).capitalize()

        result['PE Detection Threshold'] = policy['detection_level'].capitalize()
        if result['PE Detection Threshold'] == 'Medium':
            result['PE Detection Threshold'] = 'Moderate'

        result['PE Prevention Threshold'] = policy['prevention_level'].capitalize()
        if result['PE Prevention Threshold'] == 'Medium':
            result['PE Prevention Threshold'] = 'Moderate'

        if 'protection_level_pua' in policy.keys():
            result['Known PUA'] = str(policy['protection_level_pua']).capitalize()

        if 'dual_use' in policy.keys():
            result['Dual use tools'] = str(policy['dual_use']).capitalize()

        if 'dde' in policy.keys():
            result['Embedded DDE in Office files'] = str(policy['dde']).capitalize()

        if 'office_macro_script_action' in policy.keys():
            result['Macro Execution'] = str(policy['office_macro_script_action']).capitalize()

        result['In-Memory Protection'] = str(policy['in_memory_protection']).capitalize()
        result['Ransomware Behavior'] = policy['ransomware_behavior'].capitalize()
        result['Arbitrary Shellcode'] = policy['arbitrary_shellcode_execution'].capitalize()
        result['Remote Code Injection'] = policy['remote_code_injection'].capitalize()
        result['Reflective DLL Injection'] = policy['reflective_dll_loading'].capitalize()
        result['.Net Reflection'] = policy['reflective_dotnet_injection'].capitalize()
        result['AMSI Bypass'] = policy['amsi_bypass'].capitalize()
        result['Credential Dumping'] = policy['credentials_dump'].capitalize()
        result['Known Payload Executionn'] = policy['known_payload_execution'].capitalize()
        result['Suspicious Script Execution'] = policy['suspiciousScriptExecution'].capitalize()

        result['Malicious PowerShell Command Execution'] = policy['maliciousPowerShellCommandExecution'].capitalize()

        if 'malicious_js_command_execution' in policy.keys():
            result['Malicious JavaScript Execution'] = str(policy['malicious_js_command_execution']).capitalize()

        result['Suspicious PowerShell Command Execution'] = policy['suspiciousPowerShellCommandExecution'].capitalize()

        if 'powershell_script_action' in policy.keys():
            result['PowerShell execution'] = policy['powershell_script_action'].capitalize()

        if 'html_applications_action' in policy.keys():
            result['HTML Applications'] = policy['html_applications_action'].capitalize()

        if 'prevent_all_activescript_usage' in policy.keys():
            if policy['prevent_all_activescript_usage'] == 'PREVENT':
                result['ActiveScript Execution - When ActiveScripts are executed'] = 'Block all using windows'
            else:
                result['ActiveScript Execution - When ActiveScripts are executed'] = 'Default Windows action'

        if 'activescript_action' in policy.keys():
            result['ActiveScript Execution - If allowed by Windows, action when non-allow-listed script runs'] = policy['activescript_action'].capitalize()


        results.append(result)
    return results


def calculate_export_file_name(policies, mt, multi_msp):
    if mt and not multi_msp:
        server_shortname = re.sub(r'[^a-z0-9]','',policies[0]['msp_name'].lower())
    else:
        server_shortname = di.fqdn.split(".",1)[0]
    file_name = f'policy_audit_{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H.%M")}_UTC_{server_shortname}.xlsx'
    return file_name


def move_df_column_to_position(df, column_name, new_position):
    column_to_move = df.pop(column_name)
    df.insert(new_position, column_name, column_to_move)
    return df


def export_results(results_df, results_df_stylized, file_name, groups_df, include_user_account_list, users_df, users_df_styliyzed, mt, multi_msp):

    with pandas.ExcelWriter(file_name) as writer:

        results_df_stylized.to_excel(writer, sheet_name='Policy Audit', index=False, na_rep='')
        for column in results_df:
            column_width = max(results_df[column].astype(str).map(len).max(), len(column)) + 1
            col_idx = results_df.columns.get_loc(column)
            writer.sheets['Policy Audit'].set_column(col_idx, col_idx, column_width)

        groups_df.to_excel(writer, sheet_name='Group List', index=False, na_rep='')
        for column in groups_df:
            column_width = max(groups_df[column].astype(str).map(len).max(), len(column)) + 1
            col_idx = groups_df.columns.get_loc(column)
            writer.sheets['Group List'].set_column(col_idx, col_idx, column_width)

        if mt and multi_msp:
            policy_list_df = results_df[['MSP Name', 'Name', 'Group Count', 'Device Count']].copy()
        else:
            policy_list_df = results_df[['Name', 'Group Count', 'Device Count']].copy()
        policy_list_df.rename(columns={'Name': 'Policy Name'}, inplace=True)

        policy_list_df.to_excel(writer, sheet_name='Policy List', index=False, na_rep='')
        for column in policy_list_df:
            column_width = max(policy_list_df[column].astype(str).map(len).max(), len(column)) + 1
            col_idx = policy_list_df.columns.get_loc(column)
            writer.sheets['Policy List'].set_column(col_idx, col_idx, column_width)

        if include_user_account_list:
            users_df_styliyzed.to_excel(writer, sheet_name='Administrator Accounts', index=False, na_rep='')
            for column in users_df:
                column_width = max(users_df[column].astype(str).map(len).max(), len(column)) + 1
                col_idx = users_df.columns.get_loc(column)
                writer.sheets['Administrator Accounts'].set_column(col_idx, col_idx, column_width)


    print('Results written to disk as', file_name, '\n')


def add_device_counts(policy_list):
    print('Collecting device data')
    devices = di.get_devices(include_deactivated=False)
    device_counts = di.count_data_by_field(devices, 'policy_id')
    print('Adding device counts to policies')
    for policy in policy_list:
        if policy['ID'] not in device_counts.keys():
            policy['Device Count'] = 0
        else:
            policy['Device Count'] = device_counts[policy['ID']]
        print('Policy', policy['ID'], 'has', policy['Device Count'], 'devices' )
    return policy_list, devices


def add_group_counts(policy_list):
    print('Collecting group data')
    groups = di.get_groups()
    group_counts = di.count_data_by_field(groups, 'policy_id')
    print('Adding group counts to policies')
    for policy in policy_list:
        if policy['ID'] not in group_counts.keys():
            policy['Group Count'] = 0
        else:
            policy['Group Count'] = group_counts[policy['ID']]
        print('Policy', policy['ID'], 'is used by', policy['Group Count'], 'groups' )
    return policy_list, groups


def get_windows_policies_internal_api():

    #establish session with server using internal/private API
    session = create_session(f'https://{di.fqdn}/')
    username = input('Username: ')
    password = input('Password: ')
    session.log_in(username, password)

    #collect policy data
    policies_via_internal_api = []
    msps = session.list_msps()
    for msp in msps.values():
        print('Gathering data via internal/private API from', msp)
        policies = msp.get_all_windows_policies()
        for policy in policies:
            #print(policy['id'], policy['name'])
            policy_data = msp.get_policy_data_by_id(policy_id=policy['id'], policy_os_num=3)
            policy.update(policy_data)
            policies_via_internal_api.append(policy)

    #return policy list
    return policies_via_internal_api


def merge_policies(policies_external_api, policies_internal_api):

    merged_policies = []

    for externalpolicy in policies_external_api:

        for internalpolicy in policies_internal_api:

            if externalpolicy['id'] == internalpolicy['id']:

                externalpolicy['enable_dcloud'] = (internalpolicy['configuration']['checkknownthreats'] == 1)

                if internalpolicy['classifications']['scanDDE'] == 2:
                    externalpolicy['dde'] = 'Prevent'
                elif internalpolicy['classifications']['scanDDE'] == 0:
                    externalpolicy['dde'] = 'Allow'

                if internalpolicy['classifications']['suspiciousScriptExecution'] == 2:
                    externalpolicy['suspiciousScriptExecution'] = 'Prevent'
                elif internalpolicy['classifications']['suspiciousScriptExecution'] == 1:
                    externalpolicy['suspiciousScriptExecution'] = 'Detect'
                elif internalpolicy['classifications']['suspiciousScriptExecution'] == 0:
                    externalpolicy['suspiciousScriptExecution'] = 'Allow'

                if internalpolicy['classifications']['maliciousPowerShellCommandExecution'] == 2:
                    externalpolicy['maliciousPowerShellCommandExecution'] = 'Prevent'
                elif internalpolicy['classifications']['maliciousPowerShellCommandExecution'] == 1:
                    externalpolicy['maliciousPowerShellCommandExecution'] = 'Detect'
                elif internalpolicy['classifications']['maliciousPowerShellCommandExecution'] == 0:
                    externalpolicy['maliciousPowerShellCommandExecution'] = 'Allow'

                if internalpolicy['classifications']['suspiciousPowerShellCommandExecution'] == 2:
                    externalpolicy['suspiciousPowerShellCommandExecution'] = 'Prevent'
                elif internalpolicy['classifications']['suspiciousPowerShellCommandExecution'] == 1:
                    externalpolicy['suspiciousPowerShellCommandExecution'] = 'Detect'
                elif internalpolicy['classifications']['suspiciousPowerShellCommandExecution'] == 0:
                    externalpolicy['suspiciousPowerShellCommandExecution'] = 'Allow'

        merged_policies.append(externalpolicy)

    return merged_policies


class MSP(object):

    def __init__(self, msp_id, name, session):
        self.msp_id = msp_id
        self.name = name
        self.session = session

    def __repr__(self):
        return "<%s %s (ID %d)>" % (self.__class__.__name__, self.name, self.msp_id)

    @staticmethod

    def get_all_policies_by_os(self, os_num: int) -> list:
        resp = self.session.make_request("/fe/getAllPolicies/{context}/%d" % self.msp_id, context="msp")
        return [item for item in resp['result'] if item['os'] == int(os_num)]

    def get_all_windows_policies(self):
        resp = self.session.make_request("/fe/getAllPolicies/{context}/%d" % self.msp_id, context="msp")
        return [item for item in resp['result'] if item['os'] == 3]

    def get_windows_policy_data(self, policy_name=None):
        policy_id = self.get_windows_policy_id(policy_name)
        data = self.session.make_request(
            "/fe/confFile/{context}/%d" % self.msp_id,
            data={"customPolicy": policy_id, "name": "P_001.json", "os": 3},
            context="msp",
        )
        return policy_id, data

    def get_policy_data_by_id(self, policy_id: int, policy_os_num: int) -> dict:
        data = self.session.make_request(
            "/fe/confFile/{context}/%d" % self.msp_id,
            data={"customPolicy": policy_id, "os": policy_os_num},
            context="msp",
        )
        return data


class DISessionBase(object):

    def __init__(self, server_url):
        self.s = requests.Session()
        self.server_url = server_url
        self.multitenancy = None
        self.context_type = None

    def make_request(self, api, data=None, files=None, method="POST", decode=True, stream=False, context=None):
        kwargs = {}
        if self.multitenancy is False:
            context = "regular"
        if context is None and self.context_type is not None:
            context = self.context_type

        url = self.server_url + self.format_api_context(api, context)
        if data is not None:
            kwargs['json'] = data
        if files is not None:
            kwargs['files'] = files
        resp = getattr(self.s, method.lower())(url, verify=False, stream=stream, **kwargs)
        resp.raise_for_status()
        if decode is True and len(resp.text) > 0:
            return json.loads(resp.text)
        return resp


    def authenticate_using_mfa(self):

        is_authenticated = self.make_request("fe/isUserAuthenticated", method="GET")

        if not is_authenticated['isUserAuthenticated']:
            authenticator_code = input('MFA code: ')
            auth = self.make_request("fe/verifyUserMultifactorAuthenticationGoogleCode", {"code": authenticator_code})


    def log_in(self, username, password):
        resp = self.make_request("fe/login", {"username": username, "password": password})

        self.authenticate_using_mfa()

        self.multitenancy = self.get_is_multitenancy()
        return resp


class DISession(DISessionBase):

    def get_is_multitenancy(self):
        user_profile = self.make_request("fe/userProfile", {})
        self.context_type = user_profile['context']['contextType']
        return self.context_type != "regular"


    def format_api_context(self, api, context):
        return api.format(context=context)


    def list_msps(self):
        if self.multitenancy is False:
            msp = MSP(1, "Default", self)
            return {1: msp}
        resp = self.make_request(
            "/fe/multiTenantChildrenContexts/integrator/1",
            data={"parentContextIdentifiers": {"id": "1", "type": "integrator"}},
        )
        return {item['contextRef']: MSP(item['contextRef'], item['name'], self) for item in resp}


def create_session(appliance_url):
    return DISession(appliance_url)


if __name__ == "__main__":
    main()

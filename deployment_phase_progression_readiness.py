# Example of how to assess readiness to progress across deployment phases
# (moving from less restrictive to more restrictive policies) based on device,
# policy, and event data. The assessment is written to disk in Excel format, and
# can be copy-pasted into move_devices.py prompts to automate moves.
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
# import required libraries
import deepinstinct3 as di, json, datetime, pandas, re, sys
from dateutil import parser

def main():

    print_readme_on_deployemnt_phases()

    config = {}

    phase = 0
    while phase not in ('1', '1.5', '2', ''):
        phase = input('Devices to evaluate are currently in what phase? [1]: ')
        if phase == '':
            phase = '1'
    config['deployment_phase'] = float(phase)

    config['min_days_since_install'] = input('Minimum days since install [7]: ')
    if config['min_days_since_install'] == '':
        config['min_days_since_install'] = 7

    config['max_days_since_last_contact'] = input('Maximum days offline [3]: ')
    if config['max_days_since_last_contact'] == '':
        config['max_days_since_last_contact'] = 3

    config['max_open_event_quantity'] = input('Maximum open events [0]: ')
    if config['max_open_event_quantity'] == '':
        config['max_open_event_quantity'] = 0

    config['ignore_suspicious_events'] = ''
    while config['ignore_suspicious_events'] not in [True, False]:
        user_input = input('YES/NO: Include Suspicious Events [YES]: ')
        if user_input.lower() == 'no':
            config['ignore_suspicious_events'] = True
        elif user_input.lower() in ['yes', '']:
            config['ignore_suspicious_events'] = False

    config['ignore_html_applications_action'] = ''
    while config['ignore_html_applications_action'] not in [True, False]:
        user_input = input('YES/NO: Ignore "HTML Applications (HTA files) and JavaScript via rundll32 executions" policy setting [NO]: ')
        if user_input.lower() == 'yes':
            config['ignore_html_applications_action'] = True
        elif user_input.lower() in ['no', '']:
            config['ignore_html_applications_action'] = False

    config['ignore_activescript_action'] = ''
    while config['ignore_activescript_action'] not in [True, False]:
        user_input = input('YES/NO: Ignore "ActiveScript execution (JavaScript & VBScript)" policy setting [NO]: ')
        if user_input.lower() == 'yes':
            config['ignore_activescript_action'] = True
        elif user_input.lower() in ['no', '']:
            config['ignore_activescript_action'] = False

    fqdn = ''
    while fqdn[-20:] != '.deepinstinctweb.com':
        fqdn = input('DI server FQDN [di-service.customers.deepinstinctweb.com]: ')
        if len(fqdn) == 0:
            fqdn = 'di-service.customers.deepinstinctweb.com'

    key = ''
    while len(key) < 256:
        key = input('API Key: ')

    print("""
All required configuration parameters have been provided. The rest of this
process runs unattended. Duration depends upon the volume of data to be analyzed
(policies, devices, and events) and can vary from 1 minute to multiple hours.
When analysis is complete, a summary will be printed here, and full results will
be written to disk as an Excel document.
    """)

    return run_deployment_phase_progression_readiness(fqdn=fqdn, key=key, config=config)


# Calculates deployment phase for a Windows policy. Non-conforming and non-Windows policies return 0.
def classify_policy(policy, config):

    if policy['os'] == 'WINDOWS':

        if policy['prevention_level'] == 'DISABLED':
            if policy['detection_level'] in ['LOW', 'MEDIUM']:
                if policy['ransomware_behavior'] == 'DETECT':
                    return 1

        elif policy['prevention_level'] in ['LOW', 'MEDIUM']:
            if policy['ransomware_behavior'] == 'PREVENT':
                if policy['in_memory_protection'] == False:
                    return 1.5

                elif policy['in_memory_protection'] == True:
                    if policy['remote_code_injection'] == 'DETECT':
                        if policy['arbitrary_shellcode_execution'] == 'DETECT':
                            if policy['reflective_dll_loading'] == 'DETECT':
                                if policy['reflective_dotnet_injection'] == 'DETECT':
                                    if policy['amsi_bypass'] == 'DETECT':
                                        if policy['credentials_dump'] == 'DETECT':
                                            if policy['html_applications_action'] == 'DETECT' or config['ignore_html_applications_action']:
                                                if policy['activescript_action'] == 'DETECT' or config['ignore_activescript_action']:
                                                    return 2

                    if policy['remote_code_injection'] == 'PREVENT':
                        if policy['arbitrary_shellcode_execution'] == 'PREVENT':
                            if policy['reflective_dll_loading'] == 'PREVENT':
                                if policy['reflective_dotnet_injection'] == 'PREVENT':
                                    if policy['amsi_bypass'] == 'PREVENT':
                                        if policy['credentials_dump'] == 'PREVENT':
                                            if policy['html_applications_action'] == 'PREVENT' or config['ignore_html_applications_action']:
                                                if policy['activescript_action'] == 'PREVENT' or config['ignore_activescript_action']:
                                                    return 3

    return 0


# Calculates search parameters for events based on current deployment phase
def get_event_search_parameters(deployment_phase):

    search_parameters = {}
    search_parameters['type'] = []

    #static parameters for all phases
    search_parameters['status'] = ['OPEN']
    search_parameters['threat_severity'] = ['MODERATE', 'HIGH', 'VERY_HIGH']

    #example of how to focus just on a specific timeframe worth of events
    #search_parameters['timestamp'] = {'from': '2022-04-24T00:00:00.000Z', 'to': '2022-05-03T00:00:00.000Z'}

    if deployment_phase in [1, 1.5]:
        search_parameters['type'].append('STATIC_ANALYSIS')
        search_parameters['type'].append('RANSOMWARE_FILE_ENCRYPTION')
        search_parameters['type'].append('SUSPICIOUS_SCRIPT_EXCECUTION')
        search_parameters['type'].append('MALICIOUS_POWERSHELL_COMMAND_EXECUTION')

        if deployment_phase == 1:
            search_parameters['action'] = ['DETECTED']
        else:
            search_parameters['action'] = ['PREVENTED']

    elif deployment_phase in [2]:
        search_parameters['action'] = ['PREVENTED', 'DETECTED']
        search_parameters['type'].append('REMOTE_CODE_INJECTION_EXECUTION')
        search_parameters['type'].append('KNOWN_SHELLCODE_PAYLOADS')
        search_parameters['type'].append('ARBITRARY_SHELLCODE')
        search_parameters['type'].append('REFLECTIVE_DLL')
        search_parameters['type'].append('REFLECTIVE_DOTNET')
        search_parameters['type'].append('AMSI_BYPASS')
        search_parameters['type'].append('DIRECT_SYSTEMCALLS')
        search_parameters['type'].append('CREDENTIAL_DUMP')

    return search_parameters


# Calculates search parameters for suspicious events based on current deployment phase
def get_suspicious_event_search_parameters(deployment_phase):

    suspicious_search_parameters = {}
    suspicious_search_parameters['status'] = ['OPEN']
    suspicious_search_parameters['file_type'] = []

    #example of how to focus just on a specific timeframe worth of events
    #suspicious_search_parameters['timestamp'] = {'from': '2022-04-24T00:00:00.000Z', 'to': '2022-05-03T00:00:00.000Z'}

    if deployment_phase in [1, 1.5]:
        #no events from suspicious events list for these phases
        suspicious_search_parameters = {}

    elif deployment_phase in [2]:
        suspicious_search_parameters['action'] = ['DETECTED']
        suspicious_search_parameters['file_type'].append('ACTIVE_SCRIPT')
        suspicious_search_parameters['file_type'].append('HTML_APPLICATION')

    return suspicious_search_parameters


def run_deployment_phase_progression_readiness(fqdn, key, config):

    print('Beginning data collection')

    di.fqdn = fqdn
    di.key = key
    di.quiet_mode = True
    config = config
    mt = di.is_server_multitenancy_enabled()

    #collect policy data
    print('\nGetting policy data from server')
    policies = di.get_policies(include_policy_data=True)

    #collect event data
    search_parameters = get_event_search_parameters(config['deployment_phase'])
    suspicious_search_parameters = get_suspicious_event_search_parameters(config['deployment_phase'])
    print('\nGetting event data from server')
    events = di.get_events(search=search_parameters)
    print(len(events), 'events were returned.')

    if not config['ignore_suspicious_events']:
        if suspicious_search_parameters != {}:
            print('\nGetting suspicious event data from server')
            suspicious_events = di.get_suspicious_events(search=suspicious_search_parameters)
            print(len(suspicious_events), 'suspicious events were returned.')
            events = events + suspicious_events

    event_counts = di.count_data_by_field(events, 'device_id')

    #collect device data
    print('\nGetting device data from server')
    devices = di.get_devices(include_deactivated=False)
    print(len(devices), 'devices were found.')

    #determine if we have data from a single MSP or multiple
    policy_msp_ids = []
    for policy in policies:
        if policy['msp_id'] not in policy_msp_ids:
            policy_msp_ids.append(policy['msp_id'])
    if len(policy_msp_ids) > 1:
        multiple_msps = True
    else:
        multiple_msps = False

    print('\nAnalyzing policy data')
    policy_evaluation_results = []
    for policy in policies:
        policy['deployment_phase'] = classify_policy(policy, config)
        if policy['os'] == 'WINDOWS':
            if policy['deployment_phase'] > 0:
                result = f"Policy '{policy['name']}' (ID {policy['id']}) is a Phase {policy['deployment_phase']} policy."
            else:
                result = f"Policy '{policy['name']}' (ID {policy['id']}) is not aligned with any defined Deployment Phase."
            if mt and multiple_msps:
                result = f"MSP '{policy['msp_name']}' (ID {policy['msp_id']}) {result}"
            print(result)
            policy_evaluation_results.append(result)

    filtered_devices = []
    for device in devices:
        for policy in policies:
            if policy['id'] == device['policy_id']:
                device['deployment_phase'] = policy['deployment_phase']
                if device['deployment_phase'] == config['deployment_phase']:
                    filtered_devices.append(device)
    excluded_device_count = len(devices) - len(filtered_devices)
    devices = filtered_devices

    print('')
    print(len(devices), 'devices are in a phase', config['deployment_phase'], 'policy.')

    if len(devices) == 0:
        print('ERROR: Aborting analysis due to zero devices to analyze.')
        sys.exit(0)

    devices_ready = []
    devices_not_ready = []

    for device in devices:
        if device['id'] not in event_counts.keys():
            device['event_count'] = 0
        else:
            device['event_count'] = event_counts[device['id']]
        device['last_contact_days_ago'] = (datetime.datetime.now(datetime.timezone.utc) - parser.parse(device['last_contact'])).days
        device['days_since_install'] = (datetime.datetime.now(datetime.timezone.utc) - parser.parse(device['last_registration'])).days


        device['progression_criteria_violations'] = []

        if device['event_count'] > int(config['max_open_event_quantity']):
            device['progression_criteria_violations'].append('More than ' + str(config['max_open_event_quantity']) + ' open events')

        if device['last_contact_days_ago'] > int(config['max_days_since_last_contact']):
            device['progression_criteria_violations'].append('Offline for more than ' + str(config['max_days_since_last_contact']) + ' days')

        if device['days_since_install'] < int(config['min_days_since_install']):
            device['progression_criteria_violations'].append('Installed less than ' + str (config['min_days_since_install']) + ' days ago')

        if len(device['progression_criteria_violations']) > 0:
            device['ready_to_move_to_next_phase'] = False
            devices_not_ready.append(device)
        else:
            device['ready_to_move_to_next_phase'] = True
            devices_ready.append(device)

    print(len(devices_ready), 'devices are ready to move to the next phase.')
    print(len(devices_not_ready), 'devices are not ready based on violating one or more of the provided criteria.')
    print(excluded_device_count, 'devices in the system were not assessed due to not being in a phase', config['deployment_phase'], 'policy.')

    #convert data to be exported to dataframes
    devices_ready_df = pandas.DataFrame(devices_ready)
    devices_not_ready_df = pandas.DataFrame(devices_not_ready)
    config_df = pandas.DataFrame(config.items())
    search_parameters_df = pandas.DataFrame(search_parameters.items())
    suspicious_search_parameters_df = pandas.DataFrame(suspicious_search_parameters.items())
    policy_evaluation_results_df = pandas.DataFrame(policy_evaluation_results)

    #prep for export
    folder_name = di.create_export_folder()
    from_deployment_phase = "{:g}".format(float(config['deployment_phase']))
    if di.is_server_multitenancy_enabled() and not multiple_msps:
        server_shortname = re.sub(r'[^a-z0-9]','',policies[0]['msp_name'].lower())
    else:
        server_shortname = di.fqdn.split(".",1)[0]
    file_name = f'deployment_phase_{from_deployment_phase}_progression_readiness_assessment_{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H.%M")}_UTC_{server_shortname}.xlsx'

    #export dataframes to Excel format
    with pandas.ExcelWriter(f'{folder_name}/{file_name}') as writer:
        devices_ready_df.to_excel(writer, sheet_name='ready_for_next_phase', index=False)
        devices_not_ready_df.to_excel(writer, sheet_name='not_ready_for_next_phase', index=False)
        config_df.to_excel(writer, sheet_name='config', index=False)
        search_parameters_df.to_excel(writer, sheet_name='event_search', index=False)
        suspicious_search_parameters_df.to_excel(writer, sheet_name='suspicious_event_search', index=False)
        policy_evaluation_results_df.to_excel(writer, sheet_name='policy_evaluation', index=False)

    print('')
    print(f'Results were exported to disk as\n{folder_name}\\{file_name}\n')

def print_readme_on_deployemnt_phases():
    print("""
--Deployment Phase Progression Readiness Evaluation--

This tool evaluates your Deep Instinct policies, events, and devices and
assesses readiness (or lack thereof) of devices to move to a subsequent
deployment phase based on criteria you provide.

The deployment phases are defined as follows:

Phase 1:
    4 features, all in detect mode:
        Static Analysis (Threat Severity on PE files set to ≥ Moderate)
        Ransomware Behavior
        Suspicious Script Execution
        Malicious PowerShell Command Execution

Phase 2
    Phase 1 features move to prevent mode
    Enable In-Memory Protection
    8 additional features, all in detect mode:
        Arbitrary Shellcode
        Remote Code Injection
        Reflective DLL Injection
        .Net Reflection
        AMSI Bypass
        Credential Dumping
        HTML Applications
        ActiveScript Execution (JavaScript & VBScript)
    1 additional feature in prevent mode:
        Known Payload Execution

Phase 3
    Phase 2 features move to prevent mode

This tool currently supports Windows devices and policies. All non-Windows
data is excluded from analysis.

A "Read Only" or greater API Key is required, and the results are written to
disk in MS Excel format.

Below you will be asked a series of configuration questions. For each
prompt, either enter a custom value or press return (enter) without entering
any value to accept the default displayed in square brackets.
""")

if __name__ == "__main__":
    main()

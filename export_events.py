# Example of how to query server for events using a set of search parameters
# and then write the results to disk as Excel document. Particularily useful for
# large data sets which exceed the 10K limit when exporting from the GUI and/or
# complex searches which may not be easily impelemtned as filters in the GUI's
# event filtering feature set.
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
import pandas, datetime
import deepinstinct3 as di

# Optional hardcoded config - if not provided, you'll be prompted at runtime
di.fqdn = 'SERVER-NAME.customers.deepinstinctweb.com'
di.key = 'API-KEY'

# Validate config and prompt if not provided above
while di.fqdn == '' or di.fqdn == 'SERVER-NAME.customers.deepinstinctweb.com':
    di.fqdn = input('FQDN of DI Server? ')
while di.key == 'API-KEY':
    di.key = input('API Key? ')

# ==============================================================================
# THIS SECTION SHOWS A SERIES OF EXAMPLES OF HOW TO USE di.get_events TO GET
# ALL OR SOME OF THE EVENTS VISIBLE TO THE PROVIDED API KEY FROM THE SERVER
# --> Leave exactly 1 call to di.get_events uncommented

# All events
#events = di.get_events()

# Example of how to filter on minimum event_id
#events = di.get_events(minimum_event_id=1001)

# Example of how to build a set of search search parameters
# --> All provided parameters must match (AND operation, not OR)
# --> Event search is exact match only (no regex/etc) with exception of timestamp
#     fields which support a range with 'from' (minimum) and 'to' (maximum)
# --> Reference API documentation (https://fqdn/api/v1) for full list of
#     available field names and values.
search_parameters = {}
#search_parameters['status'] = ['OPEN', 'CLOSED']
#search_parameters['threat_severity'] = ['LOW', 'MODERATE', 'VERY_HIGH']
#search_parameters['trigger'] = ['BRAIN', 'DDE_USAGE']
#search_parameters['type'] = ['STATIC_ANALYSIS', 'SCRIPT_CONTROL_COMMAND', 'SCRIPT_CONTROL_PATH', 'RANSOMWARE_FILE_ENCRYPTION', 'SUSPICIOUS_SCRIPT_EXCECUTION', 'MALICIOUS_POWERSHELL_COMMAND_EXECUTION', 'SUSPICIOUS_POWERSHELL_COMMAND_EXECUTION']
#search_parameters['timestamp'] = {'from': '2021-05-01T15:35:11.333Z', 'to': '2021-05-03T15:35:11.333Z'}
search_parameters['insertion_timestamp'] = {'from': '2021-07-01T00:00:00.000Z', 'to': '2023-07-01T00:00:00.000Z'}
#search_parameters['last_reoccurence'] = {'from': '2021-01-16T15:35:11.333Z', 'to': '2021-02-23T15:35:11.333Z'}
#search_parameters['close_timestamp'] = {'from': '2021-01-17T15:35:11.333Z', 'to': '2021-02-17T15:35:11.333Z'}
#search_parameters['close_trigger'] = ['NONE','BRAIN']
#search_parameters['reoccurence_count'] = 7
#search_parameters['last_action'] = ['FILE_UPLOADED_SUCCESSFULLY', 'FILE_UPLOADED_FAILED']
#search_parameters['comment'] = 'Hello World'
#search_parameters['msp_name'] = 'My MSP Name'
#search_parameters['msp_id'] = 651
#search_parameters['tenant_name'] = 'Patrick Lab'
#search_parameters['tenant_id'] = 612
#search_parameters['file_hash'] = '9e7878355f2481e338ea8162bebadb74e97cdf5cbc06e54b69215377fc82d30d'
#search_parameters['file_type'] = ['EICAR', 'PE', 'DOC', 'ZIP', 'EXE', 'RAR', 'JAR', 'SWF']
#search_parameters['file_archive_hash'] = '2cf6bb71013ce46eb9f9c5caf52aa400f76a679cf62407dbb245e87086714178'
#search_parameters['path'] = 'c:\foo\bar.dll'
#search_parameters['certificate_thumbprint'] = 'a3958ae522f3c54b878b20d7b0f63711e08666b2'
#search_parameters['certificate_vendor_name'] = 'Google LLC'
#search_parameters['deep_classification'] = ['RANSOMWARE', 'BACKDOOR', 'DROPPER']
#search_parameters['file_status'] = ['UPLOADED', 'NOT_UPLOADED']
#search_parameters['sandbox_status'] = ['NOT_READY_TO_GENERATE', 'READY_TO_GENERATE']
#search_parameters['file_size'] = 12345
events = di.get_events(search=search_parameters)

# Example of combining search parameters plus minimum event_id
#TODO: Build search_parameters dictionary based upon example above
#events = di.get_events(search=search_parameters, minimum_event_id=5001)

# ==============================================================================

if len(events) > 0:
    # Convert event data to a Pandas data frame for easier manipulation and export
    events_df = pandas.DataFrame(events)
    # Sort the data frame by event id
    events_df.sort_values(by=['id'], inplace=True)

    # Export the data frame to disk in Excel format

    # Calculate folder and file name
    folder_name = di.create_export_folder()
    file_name = f'events_{datetime.datetime.today().strftime("%Y-%m-%d_%H.%M")}.xlsx'

    # Write data to disk
    events_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print('INFO:', len(events), 'events were exported to disk as:', f'{folder_name}/{file_name}')

else:  #No events were found
    print('No events were found on the server')

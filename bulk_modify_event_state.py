# Example of how to bulk manage event state. It overs two workflows:
# (A) Ingest an Excel format document containing a list of events to modify.
# -or-
# (B) Query the server for live data by pulling all events, then applying
#     client-side filtering and taking action on the events that match criteria
#     that you define. For this workflow, a preview in the form of an export of
#     the matching events is written to disk in Excel format for review before
#     confirming the change.
# Supports taking one or more of these actions: open, close, archive, unarchive.
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
import deepinstinct3 as di, json, datetime, pandas, sys
from dateutil import parser


def main():

    di.fqdn = input('Enter FQDN of DI Server, or press enter to accept the default [di-service.customers.deepinstinctweb.com]: ')
    if di.fqdn == '':
        di.fqdn = 'di-service.customers.deepinstinctweb.com'

    di.key = input('Enter API Key for DI Server: ')

    prebuilt_list = ''
    while prebuilt_list not in [True, False]:
        user_response = input('Do you have a prebuilt list of events to modify [YES | NO]? ')
        if user_response.lower() == 'yes':
            prebuilt_list = True
        elif user_response.lower() == 'no':
            prebuilt_list = False

    if prebuilt_list:
        events_file_name = input('Enter name of file containing events to modify, or press enter to accept the default [events.xlsx]: ')
        if events_file_name == '':
            events_file_name = 'events.xlsx'
        event_id_list = get_event_ids_from_file(events_file_name)

    else:
        event_id_list = get_event_ids_based_on_live_data()

    close_events = ''
    while close_events not in [True, False]:
        user_response = input('Do you want to CLOSE these events [YES | NO]? ')
        if user_response.lower() == 'yes':
            close_events = True
        elif user_response.lower() == 'no':
            close_events = False

    archive_events = ''
    while archive_events not in [True, False]:
        user_response = input('Do you want to ARCHIVE these events [YES | NO]? ')
        if user_response.lower() == 'yes':
            archive_events = True
        elif user_response.lower() == 'no':
            archive_events = False

    open_events = ''
    while open_events not in [True, False]:
        user_response = input('Do you want to OPEN these events [YES | NO]? ')
        if user_response.lower() == 'yes':
            open_events = True
        elif user_response.lower() == 'no':
            open_events = False

    unarchive_events = ''
    while unarchive_events not in [True, False]:
        user_response = input('Do you want to UNARCHIVE these events [YES | NO]? ')
        if user_response.lower() == 'yes':
            unarchive_events = True
        elif user_response.lower() == 'no':
            unarchive_events = False


    #break event_id_list into a list of smaller lists
    batch_size = 250
    event_id_list_broken_into_batches = [event_id_list[i:i + batch_size] for i in range(0, len(event_id_list), batch_size)]
    print('\nINFO: The', len(event_id_list), 'event IDs have been broken into', len(event_id_list_broken_into_batches), 'batches of', batch_size)

    #iterate through the batches of event ids
    batch_number = 1
    for batch in event_id_list_broken_into_batches:
        print('Processing batch', batch_number, 'of', len(event_id_list_broken_into_batches))

        if close_events:
            print('  Closing', len(batch), 'events')
            di.close_events(batch)

        if archive_events:
            print('  Archiving', len(batch), 'events')
            di.archive_events(batch)

        if open_events:
            print('  Opening', len(batch), 'events')
            di.open_events(batch)

        if unarchive_events:
            print('  Unarchiving', len(batch), 'events')
            di.unarchive_events(batch)

        batch_number += 1


def get_event_ids_based_on_live_data():

    #get all events from server
    all_events = di.get_events()
    print('INFO:', len(all_events), 'total visible events on server')

    filtered_events = []
    for event in all_events:

    # !!! TODO !!! - Modify code  below to set search parameters(s) for events to modify
    # --------------------------------------------------------------------------
        if event['status'] in ['OPEN']:
            if event['recorded_device_info']['hostname'] in ['HOSTNAME01']:
                if event['type'] == ['REFLECTIVE_DOTNET']:
                    if event['path'] in ['C:\\Program Files (x86)\\Microsoft SQL Server\\100\\DTS\\Binn\\DTExec.exe']:
                        filtered_events.append(event)
            if event['type'] == ['AMSI_BYPASS']:
                if event['path'] in ['C:\\Program Files (x86)\\Microsoft SQL Server\\100\\DTS\\Binn\\SQLPS.exe']:
                    filtered_events.append(event)
        if event['type'] == ['STATIC_ANALYSIS']:
            if event['path'] in ['C:\\Users\\user\\Desktop\\PANDAFREEAV - Copy.exe']:
                filtered_events.append(event)
    # --------------------------------------------------------------------------

    #write preview of events to be modified to disk
    filtered_events_df = pandas.DataFrame(filtered_events)
    folder_name = di.create_export_folder()
    file_name = f'modified_events_{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H.%M")}_UTC.xlsx'
    filtered_events_df.to_excel(f'{folder_name}/{file_name}', index=False)
    print('INFO:', len(filtered_events), 'events found matching defined criteria and have been written to disk as', f'{folder_name}/{file_name}. Please review before proceeding to confirm expected results.')

    #strip out event ids from filtered_events
    event_id_list = []
    for event in filtered_events:
        event_id_list.append(event['id'])

    return event_id_list


def get_event_ids_from_file(file_name):
    print('INFO: Importing events from', file_name)
    dataframe = pandas.read_excel(file_name)
    event_id_list = dataframe['id'].values.tolist()
    print('INFO: Found', len(event_id_list), 'event ids in provided input file.')
    return event_id_list


if __name__ == "__main__":
    main()

# Example of how to build a custom integration for event forwarding, in this
# example reading events using the REST API and forwarding them to Slack using
# a Slack Incoming Webhook.
#
# USAGE
# 1. Save the latest version of both this file (event_forwarder_slack.py) and
#    the DI API Wrapper (deepinstinct3.py) to the same folder on disk.
# 2. Review and adjust configuration in-line below, then save changes.
# 3. By default the script will pull all events matching your configured search
#    parameters. To start at a specific event ID, save that ID as a file
#    'event_forwarder_slack.conf' in the same directory as the script.
# 3. Execute the script with this command: python event_forwarder_slack.py

# NOTE: In order to avoid re-sending the same events, the script maintains a
#       record of the last event previously sent on disk. This is stored in
#       'event_forwarder_slack.conf' in the same directory as the script. This
#       allows preservation of this "high water mark" even if the script is
#       killed and restarted. Be cautious not to delete/rename/move the .conf
#       file. Doing so will cause the script to re-send all events.

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

#---import required libraries---
import time, json, requests, datetime, deepinstinct30 as di


#---configuration---
di.fqdn = 'FOO.customers.deepinstinctweb.com'
di.key = 'BAR'

# Define sleep time between queries to server in seconds (default 5 minutes)
sleep_time_in_seconds = 300

# Define a webhook URL for sending event data to Slack
webhook_url = 'https://hooks.slack.com/workflows/REDACTED'

# Define a list of fields to remove from events before sending to Slack
fields_to_remove = ['msp_name', 'msp_id', 'tenant_name', 'tenant_id',
                    'mitre_classifications',
                    'recorded_device_info',
                    'file_status', 'sandbox_status']

# Define search parameters when querying DI server for new events
search_parameters = {}
#search_parameters['status'] = ['OPEN', 'CLOSED']
#search_parameters['type'] = ['STATIC_ANALYSIS', 'RANSOMWARE_FILE_ENCRYPTION']
#search_parameters['threat_severity'] = ['HIGH', 'VERY_HIGH']


#---define methods used at runtime---

# a method for forwarding a single event to Slack using the provided webhook_url
def send_event_to_slack(event):
    slack_data = {'event_data': json.dumps(event, indent=4)}
    response = requests.post(webhook_url, json=slack_data, headers={'Content-Type': 'application/json'})

# a method to remove a key from a dictionary if it is present
def remove_key(dict, key):
    if key in dict:
        dict.pop(key)

# a method to remove unwanted fields from event data
def sanitize_event(event):
    for field in fields_to_remove:
        remove_key(event, field)

# a method to read config from .conf file on disk
def get_config():
    try:
        with open('event_forwarder_slack.conf', 'r') as f:
            return int(f.read())
    except OSError as e:
        return 0

# a method to write config to .conf file on disk
def save_config(event_id):
    try:
        with open('event_forwarder_slack.conf', 'w') as f:
            f.write(str(event_id))
    except OSError as e:
        now = datetime.datetime.now()
        print(now.strftime("%H:%M"), 'ERROR:', e)


#---runtime---
while True:
    max_event_processed_previously = get_config()
    print('Getting new events with id greater than', max_event_processed_previously)

    try:
        new_events = di.get_events(minimum_event_id=max_event_processed_previously, search=search_parameters)
    except requests.exceptions.RequestException as e:
        now = datetime.datetime.now()
        print(now.strftime("%H:%M"), 'ERROR:', e)
        new_events = []

    print(len(new_events), 'events were returned')

    if len(new_events) > 0:

        for event in new_events:
            sanitize_event(event)
            print('Sending event', event['id'], 'to Slack')
            try:
                send_event_to_slack(event)
            except requests.exceptions.RequestException as e:
                now = datetime.datetime.now()
                print(now.strftime("%H:%M"), 'ERROR:', e)
            if event['id'] > max_event_processed_previously:
                max_event_processed_previously = event['id']

        print('max_event_processed_previously is now', max_event_processed_previously)
        save_config(max_event_processed_previously)

    print('Sleeping for', sleep_time_in_seconds, 'seconds')
    time.sleep(sleep_time_in_seconds)

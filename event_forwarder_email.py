# Example of how to build your own e-mail forwarder, meaning you can define
# exactly what events you want to send and to who and with what template.
# This sample uses https://pypi.org/project/yagmail/ to send e-mail using a
# GMail account, but you can replace the  send_event_via_email method with your
# own code to use any library and e-mail service of your choice.
#
# USAGE
# 1. Save the latest version of both this file (event_forwarder_email.py) and
#    the DI API Wrapper (deepinstinct3.py) to the same folder on disk.
# 2. Review and adjust configuration in-line below, then save changes.
# 3. By default the script will pull all events matching your configured search
#    parameters. To start at a specific event ID, save that ID as a file
#    'event_forwarder_email.conf' in the same directory as the script.
# 4. Optionally replace or modify the send_event_via_email() method to use
#    any mail template, library, or service of your choosing.
# 5. Execute the script with this command: python event_forwarder_email.py
#
# NOTE: In order to avoid re-sending the same events, the script maintains a
#       record of the last event previously sent on disk. This is stored in
#       'event_forwarder_email.conf' in the same directory as the script. This
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
#
#---import required libraries---
import time, json, requests, datetime, yagmail, deepinstinct30 as di


#---configuration---

# Deep Instinct server
di.fqdn = 'FOO.customers.deepinstinctweb.com'
di.key = 'BAR'

# GMail account (used as SMTP relay)
username = 'USERNAME@gmail.com'
password = 'PASSWORD'

# Where to send the e-mails
recepient = 'USER@DOMAIN'

# Define sleep time between queries to server in seconds (default 5 minutes)
sleep_time_in_seconds = 300

# Define a list of fields to remove from events before sending the e-mail
fields_to_remove = []

# Define search parameters when querying DI server for new events
search_parameters = {}
#search_parameters['status'] = ['OPEN', 'CLOSED']
#search_parameters['type'] = ['STATIC_ANALYSIS', 'RANSOMWARE_FILE_ENCRYPTION']
#search_parameters['threat_severity'] = ['HIGH', 'VERY_HIGH']


#---define methods used at runtime---

# a method for forwarding a single event via e-mail
def send_event_via_email(event, recepient):

    subject_line = f"New DI event on {event['recorded_device_info']['hostname']} of type {event['type']} (ID {event['id']}) | {di.fqdn}"
    body = json.dumps(event, indent=4)

    try:
        yag = yagmail.SMTP(username,password)
        yag.send(recepient,subject_line,body)
    except:
        print('Error sending e-mail')
    else:
        print('Email was sent successfully')

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
        with open('event_forwarder_email.conf', 'r') as f:
            return int(f.read())
    except OSError as e:
        return 0

# a method to write config to .conf file on disk
def save_config(event_id):
    try:
        with open('event_forwarder_email.conf', 'w') as f:
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
            print('Sending event', event['id'], 'to', recepient)
            try:
                send_event_via_email(event, recepient)
            except requests.exceptions.RequestException as e:
                now = datetime.datetime.now()
                print(now.strftime("%H:%M"), 'ERROR:', e)
            if event['id'] > max_event_processed_previously:
                max_event_processed_previously = event['id']

    print('max_event_processed_previously is now', max_event_processed_previously)
    save_config(max_event_processed_previously)
    print('Sleeping for', sleep_time_in_seconds, 'seconds')
    time.sleep(sleep_time_in_seconds)

# Example of how to build a custom integration to pull new Audit Log entries
# at a defined interval and then push them to a Slack channel.
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
import time, json, requests, datetime, deepinstinct30 as di
from dateutil import parser

#---configuration---
di.fqdn = 'SERVERNAME.customers.deepinstinctweb.com'
di.key = 'API-KEY'
slack_webhook_url = 'https://hooks.slack.com/workflows/WEBHOOK-URL'
sleep_time_in_seconds = 300
categories=['LOGIN', 'FAILED_LOGIN', 'LOGOUT', 'NOTIFICATION', 'COMMENT', 'ADMINISTRATOR_MANAGEMENT', 'POLICY', 'ALLOW_LIST_DENY_LIST', 'GROUP', 'SYSTEM_SETTINGS', 'DEPLOYMENT', 'SYSTEM_REPORT_SEEN', 'SANDBOX_REPORT', 'BACKUP_AND_RESTORE', 'REMEDIATION', 'SERVER_TLS_CERTIFICATE', 'REPORTING']
persistent_config_file_name = f'audit_log_forwarder_slack_{di.fqdn.split(".",1)[0]}.conf'

# a method for forwarding a single Audit Log to Slack using the provided webhook_url
def send_to_slack(entry, simulate=False):
    slack_data = {  'timestamp': parser.parse(entry['timestamp']).strftime("%Y-%m-%d %H:%M:%S %Z"),
                    'user': entry['user_id'],
                    'category': entry['category'].capitalize(),
                    'type': entry['type'].capitalize(),
                    'source': entry['source'],
                    'text': entry['description']
                }
    if simulate:
        print('The following data would have been sent to', slack_webhook_url, '\n', json.dumps(slack_data,indent=4))
    else:
        requests.post(slack_webhook_url, json=slack_data, headers={'Content-Type': 'application/json'})

# a method to read config from .conf file on disk
def get_config():
    try:
        with open(persistent_config_file_name, 'r') as f:
            return int(f.read())
    except OSError as e:
        return 0

# a method to write config to .conf file on disk
def save_config(offset):
    try:
        with open(persistent_config_file_name, 'w') as f:
            f.write(str(offset))
    except OSError as e:
        now = datetime.datetime.now()
        print(now.strftime("%H:%M"), 'ERROR:', e)


#---runtime---
while True:
    offset = get_config()
    print('Getting new entries with id greater than', offset)

    try:
        new_entries = di.get_audit_log(offset=offset, categories=categories)
    except requests.exceptions.RequestException as e:
        now = datetime.datetime.now()
        print(now.strftime("%H:%M"), 'ERROR:', e)
        new_entries = []

    print(len(new_entries), 'items were returned')

    if len(new_entries) > 0:

        for entry in new_entries:
            print('Sending entry', entry['id'], 'to Slack')
            try:
                send_to_slack(entry)
                #send_to_slack(entry, simulate=True)
            except requests.exceptions.RequestException as e:
                now = datetime.datetime.now()
                print(now.strftime("%H:%M"), 'ERROR:', e)
            if entry['id'] > offset:
                offset = entry['id']

        print('Highest Audit Log Entry ID is now', offset)
        save_config(offset)

    print('Sleeping for', sleep_time_in_seconds, 'seconds')
    time.sleep(sleep_time_in_seconds)

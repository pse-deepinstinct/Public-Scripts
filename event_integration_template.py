# Generic template for building custom integrations with events in a standalone
# Python file (no need for API Wrapper). Shows how to query the server for new
# events at a 5 minute intervals. Just drop in code for whatever you want to do
# with those events.

# Import required libraries
import requests, time, json


# Define server configuration
fqdn = 'FOO.customers.deepinstinctweb.com'
key = 'BAR'


# Runtime

highest_event_id_collected_previously = 0

while True:

    last_id = highest_event_id_collected_previously

    while last_id != None:

        request_url = f'https://{fqdn}/api/v1/events/?after_event_id={last_id}'
        response = requests.get(request_url, headers={'accept': 'application/json', 'Authorization': key})

        if response.status_code == 200:

            if 'last_id' in response.json():
                last_id = response.json()['last_id']
            else:
                last_id = None

            if 'events' in response.json():
                events = response.json()['events']
                print('INFO: Found', len(events), 'events on query to', request_url)
                for event in events:
                    if event['id'] > highest_event_id_collected_previously:
                        highest_event_id_collected_previously = event['id']

                    #TODO: Insert code here to ingest data in SIEM, generate e-mail, or take
                    #      other desired action. For now the placeholder pretty-prints event
                    #      to console.
                    print(json.dumps(event, indent=4), '\n')

        else:
            print('ERROR: Unexpected return code', response.status_code, 'on GET', request_url)
            time.sleep(15)


    print('INFO: Sleeping for 5 minutes')
    time.sleep(300)

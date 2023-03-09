# Example of how to build automated alarms for potential operation problems.
# This example periodically (at defined interval) reads device list data and
# calculates what percent of devices are online versus offline. When offline
# percentage (ratio) exceeds a defined limit, it can be configured to throw
# an alarm.
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
import deepinstinct25 as di, time, json

# Optional hardcoded config - if not provided, you'll be prompted at runtime
di.fqdn = 'SERVER-NAME.customers.deepinstinctweb.com'
di.key = 'API-KEY'

# Validate config and prompt if not provided above
while di.fqdn == '' or di.fqdn == 'SERVER-NAME.customers.deepinstinctweb.com':
    di.fqdn = input('FQDN of DI Server? ')
while di.key == '' or di.key == 'API-KEY':
    di.key = input('API Key? ')

# Run indefinitely
while True:

    # Get device data from server
    devices = di.get_devices()

    # Create counters for each category of devices
    results = {}
    results['online_count'] = 0
    results['offline_count'] = 0

    # Iterate through all devices, count devices
    for device in devices:
        # Count devices consuming a license only
        if device['license_status'] == 'ACTIVATED':
            # Check connectivity status and increment the matching counter
            if device['connectivity_status'] == 'ONLINE':
                results['online_count'] += 1
            elif device['connectivity_status'] == 'OFFLINE':
                results['offline_count'] += 1

    # Calculate ratio of offline devices
    results['ratio_offline'] = results['offline_count'] / (results['offline_count'] + results['online_count'])

    # Print results to console
    print(json.dumps(results, indent=4))

    # Define warning trigger here
    if results['ratio_offline']  > 0.3:
        print('WARNING: More than 30% of devices are offline')
        # TODO:
        # Add code here to send an e-mail alert, send a Slack messgage,
        # or take other desired action

    # Sleep for 6 hours (21600 seconds) before repeating
    time.sleep(21600)

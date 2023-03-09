# Example of how to programatically identify and download the latest available
# client installer. This could be used, for example, by a deployment tool to
# ensure that the latest available version is always downloaded from the server
# before an installation. It could also be used to populate an internal
# repository for manual installations in break/fix scenarios.
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
#import libraries
import requests, json

#server config
fqdn = 'FOO.customers.deepinstinctweb.com'
key = 'BAR'

#get list of versions from server
request_url = f'https://{fqdn}/api/v1/deployment/agent-versions'
request_headers = {'Authorization': key, 'accept': 'application/json'}
response = requests.get(request_url, headers=request_headers)
available_versions = response.json()

print('These are all the available versions on the server', fqdn)
print(json.dumps(available_versions, indent=4))


#calculate what the latest available Windows version is
highest_windows_version = {'version': '0'}
for version in available_versions:
    if version['os'] == 'WINDOWS':
        if version['version'] > highest_windows_version['version']:
            highest_windows_version = version

print('This is the highest numbered Windows version on the server', fqdn)
print(json.dumps(highest_windows_version, indent=4))


#download the latest available Windows version
request_url = f'https://{fqdn}/api/v1/deployment/download-installer'
request_headers = {'Authorization': key, 'accept': 'application/json', 'Content-Type': 'application/json'}
response = requests.post(request_url, headers=request_headers, json=highest_windows_version)

#write it to disk
file_name = f"deepinstinct_{highest_windows_version['os'].lower()}_{highest_windows_version['version']}.exe"
with open(file_name, 'wb') as f:
    f.write(response.content)

print('The installer was saved to disk as', file_name)

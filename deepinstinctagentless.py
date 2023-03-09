# Library file which defines methods for sending files to agentless for scanning
# and returns verdict.
# For DPA 3.X
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

#Import required libraries
import requests, base64, json, urllib3

#Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Primary method which accepts file name and optional config data, submits scan, simplifies it, and returns result
def scan_file(file_name, scanner_ip, simplified=False, encoded=False, scanner_port=5000, protocol='https'):

    # read file from disk (rb means opens the file in binary format for reading)
    with open(file_name, 'rb') as f:
        #read file
        data = f.read()
        #close file
        f.close()

    if encoded:
        #encode data and set URL to match
        data = base64.b64encode(data)
        request_url = f'{protocol}://{scanner_ip}:{scanner_port}/scan/base64'
    else:
        #leave data as-is and set URL to match
        request_url = f'{protocol}://{scanner_ip}:{scanner_port}/scan/binary'

    # send scan request, capture response
    response = requests.post(request_url, data=data, timeout=20, verify=False)

    # validate response code and proceed if expected value 200
    if response.status_code == 200:
        #convert to Python dictionary
        verdict = response.json()
        if simplified:
            #Call function to simplify the verdict
            verdict = simplify_verdict(verdict)
        #Return [simplified] verdict
        return verdict
    else:
        print('ERROR: Unexpected return code', response.status_code, 'on POST to', request_url)
        return None


#Wrapper which invokes scan_file with the parameter to use encoding
def scan_file_encoded(file_name, scanner_ip, simplified=False):
    return scan_file(file_name=file_name, scanner_ip=scanner_ip, simplified=simplified, encoded=True)


# A method used to convert the raw verdict received from DI Agentless into a simplified/more user-friendly format
# --> Recommend to use this with an Agentless Policy where "prevention" is enabled at Threat Severity "Low" and above
# --> This method introduces the concept of a "Suspicious" verdict, which is for files that score Low or Moderate
def simplify_verdict(verdict):

    if 'verdict' not in verdict.keys():
        print('ERROR: The verdict passed to simplify_verdict is missing or corrupt:\n', verdict)
        return None

    else:
        #remove the redundent text 'filetype' from the file type value, if present
        if 'file_type' in verdict.keys():
            verdict['file_type'] = verdict['file_type'].replace('FileType','')

        if verdict['verdict'] == 'Malicious':

            if verdict['severity'] in ['VERY_HIGH', 'HIGH']:

                return {'verdict': 'Malicious',
                        'file_type': verdict['file_type'],
                        'threat_severity': verdict['severity'],
                        'file_hash': verdict['file_hash'],
                        'scan_guid': verdict['scan_guid']}

            else:

                return {'verdict': 'Suspicious',
                        'file_type': verdict['file_type'],
                        'threat_severity': verdict['severity'],
                        'file_hash': verdict['file_hash'],
                        'scan_guid': verdict['scan_guid']}

        elif verdict['verdict'] == 'Benign':

            return {'verdict': 'Benign',
                    'file_type': verdict['file_type'],
                    'file_hash': verdict['file_hash'],
                    'scan_guid': verdict['scan_guid']}

        elif verdict['verdict'] == 'Not Classified':
            return {'verdict': 'Unsupported',
                    'file_type': 'Other',
                    'scan_guid': verdict['scan_guid']}

        else:
            print('WARNING: Error in processing verfict passed to simplify_verdict:\n', verdict)
            return None

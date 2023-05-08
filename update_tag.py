# update_tag.py
# v1.05 - April 2023
# Created by David Ramirez
# Updated and maintained by Deep Instinct Professional Services
#
#
# Accepts a *.csv of hostname and desired tag.  Finds matching device IDs and then
# updates the current tag of the devices.
# NOTE 1: Even when using exact hostnames, there may be multiple matches found, 
#         and in that case all matching regex_hostname_search will have their tag updated.
#
# NOTE 2: If group rules using TAGS is in place, updating device tags will cause
#         related groups to be updated immediately.
#
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


import argparse
import requests
import urllib3
import json
import csv

def main():


    # Define CLI paramters
    parser = argparse.ArgumentParser(description="Update 'tag' of devices specified in the CSV")
    parser.add_argument("-file", dest="filename",
                        type=str, required=True,
                        help="Input filename/path of the CSV, which has two columns, device ids and desired tag")
    parser.add_argument("-server", dest="di_fqdn",
                        type=str, required=True,
                        help="Appliance FQDN, e.g. id-int.deepinstinctweb.com")
    parser.add_argument("-apikey", dest="apikey",
                        type=str, required=True,
                        help="API key for appliance")

    # Store input data
    args = parser.parse_args()

    # Assign input file to a variable
    csv_file = (args.filename)

    #  Create dictionary and import the csv file
    result = {}
    with open(csv_file,'r') as input_file:
         csv_reader = csv.reader(input_file)
         for row in csv_reader:
              result[int(row[0])] = row[1]

    # For troublshooting, verify file was imported as dictionary properly
    # print (result)

    # STATIC HEADERS / DO NOT MODIFY
    headers = {}
    headers['accept'] = 'application/json'
    headers['Authorization'] = args.apikey

    # Begin loop to modify device tag one by one
    print("Beginning Tag update process...\n")


    for device_id, new_tag in result.items():
        request_url = f'https://{args.di_fqdn}/api/v1/devices/{device_id}/tag'
        payload = {"tag" : new_tag}
        print("Sending payload...")
        response = requests.patch(request_url, headers=headers, json=payload)
        if response.status_code == 204:
            print('Successfully updated device tag.\n')
        elif response.status_code == 403:
            print("ERROR: Device ID does not belong to connector's MSP\n")
        else:
            print('ERROR: Unexpected response', response.status_code, 'on PUSH to', request_url, 'with payload', payload,'\n')


if __name__ == "__main__":
     import sys
     sys.exit(main())
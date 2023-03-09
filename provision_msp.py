# This script provides an example of how to use the Deep Instinct REST API
# to provision new MSPs on a multi-tenancy server, including pre-populating
# them with a set of policies based upon a template MSP.

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

# PREREQUISITES
# 1. Python 3.8 or later
# 2. Deep Instinct REST API Wrapper
# 3. Third-party libraries (strongly recommend to install Anaconda)
# 4. Network access to management server on port 443
# 5. Multi-tenancy enabled D-Appliance (management server)
# 6. A Full Access API key for all MSPs

# KNOWN LIMITATIONS AND USAGE NOTES
# Only policy settings that are available to read and write via the
# DI REST API are migrated. Any settings not visible via the API remain
# at their defailts in the destination policies. As of December 2021, the
# non-visible fields in Windows policies are:
# 1. Enable D-Cloud services
# 2. Embedded DDE object in Microsoft Office document
# 3. Suspicious Script Execution
# 4. Malicious PowerShell Command Execution
# 5. Suspicious Activity Detection
# 6. Suspicious PowerShell Command Execution
# 7. Integrate D-Client with Windows Security Center
# 8. Permitted connections for network isolated devices
# 9. Gradual Deployment
# For up-to-date information, reference the WindowsPolicyData model in the API
# documentation on your DI server. If/when additional fields are added, this
# script will automatically migrate them.

# USAGE
# 1. Save the latest version of both this file (provision_msp.py) and
#    the DI API Wrapper (deepinstinct3.py) to the same folder on disk.
# 2. Edit this file to provide the customer name, license count, server, api
#    key, and the id of the template msp in-line below.
# 3. Execute the script with this command:  python provision_msp.py

import deepinstinct3 as di
import json

#define details of the new customer
customer_name = 'Mos Eisley Cantina'
license_count = 327

#define which already-existing MSP on the server is the template (to copy policies from)
template_msp_id = 1

#set server name (must be a MULTI-TENANCY enabled D-Appliance)
di.fqdn = 'foobar.customers.deepinstinctweb.com'

#define API keys to use (both must be created in DI Hub and have access to All MSPSs)
full_access_key = 'alice'
account_management_key = 'bob'

#create new msp for the customer and one tenant within it
di.key = full_access_key
new_msp = di.create_msp(customer_name, license_count)
new_tenant = di.create_tenant(customer_name, license_count, new_msp['name'])

#pretty-print the new Tenant information, which includes activation tokens
print(json.dumps(new_tenant, indent=4))

#create a user within the new MSP
di.key = account_management_key
di.create_user(username='wuher', password='NoDroids1!', first_name='Wuher', last_name='The Bartender', email='wuher@tatooine.is', role='MASTER_ADMINISTRATOR', msp_id=new_msp['id'])

#copy the policy data from the template to the new MSP
di.key = full_access_key
di.migrate_policies(source_msp_id=template_msp_id, destination_msp_id=new_msp['id'])

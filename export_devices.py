# Export devices.
# Created by DI PSE March 1,2023
# V1.0
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

import pandas, datetime
import deepinstinct3 as di

# Optional hardcoded config - if not provided, you'll be prompted at runtime
di.fqdn = 'FQDN of D-Appliance'
di.key = 'API Key'

# Validate config and prompt if not provided above
while di.fqdn == '' or di.fqdn == 'SERVER-NAME.customers.deepinstinctweb.com':
    di.fqdn = input('FQDN of DI Server? ')
while di.key == 'API-KEY':
    di.key = input('API Key? ')

# ==============================================================================
# Get Devices call
devices = di.export_devices(include_deactivated=False)

# ==============================================================================

# Export devices.
# Created by DI PSE March 1,2023
# V1.0

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

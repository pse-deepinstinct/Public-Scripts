# deepinstinct_rest_api_wrapper
Open source API Wrapper (Python Bindings) for Deep Instinct REST API + associated samples

Compatibility:
* deepinstinct3 - Designed for and tested using Deep Instinct D-Appliance version 3.x
* deepinstinct25 - Designed for and tested using Deep Instinct D-Appliance version 2.5.x
* deepinstinctagentless - Designed for and tested against Deep Instinct Agentless Connector version 2.3.2.0p
* All of above written and tested using a Python 3.8.3 instance installed by Anaconda

Suggested Usage:

1. Save deepinstinct*.py in the same directory as your own code
2. Depending upon which version of the Deep Instinct D-Appliance or Deep Instinct Agentless Connector you are interacting with, include one of the following at the top of your code:
   import deepinstinct3 as di
   or
   import deepinstinct25 as di
   or
   import deepinstinctagentless as di
3. Set/modify the DI server name like this: di.fqdn = 'SERVER-NAME' (not applicable to Agentless Connector)
4. Set/modify the DI REST API key like this: di.key = 'API-KEY' (not applicable to Agentless Connector)
5. Set/modify the Deep Instinct Agentless Connector like this: di.agentless_connector = 'IP-ADDRESS-OR-DNS-NAME' (not applicable to D-Appliance)
6. Invoke the REST API methods like this:  di.function_name(arg1, arg2). Reference source code and in-line comments for details.
7. For testing and interactive usage, I use and recommend Jupyter Notebook, which is installed as part of Anaconda (https://www.anaconda.com/)
8. I highly recommend to reference the samples provided in this project (all files not matching deepinstinct*.py) for examples of how to import and use the API Wrapper as described above.

Notes/Disclaimer:
The owner of this repository is no longer associated with Deep Instinct Ltd. (the vendor). Nothing in this repository is a commercial or supported product by myself, the vendor, or any organization for that matter! This repository is provided under GNU General Public License v3.0. This code is provided as a [hopefully] useful set of examples and base code to assist you with writing code to instrument your own custom logic against Deep Instinct REST APIs in both the management server (D-Appliance) and Agentless scanners, and also for education of the broader community on how to interact with RESTful APIs in general (not specific to any specific vendor). It is provided AS-IS/NO WARRANTY. This code often has limited error checking and logging, and likely contains defects or other deficiencies. Test thoroughly first, and use at your own risk. This API Wrapper is not a Deep Instinct commercial product and is not officially supported, although the underlying REST API is. If/when you encounter an issue, I suggest to remove the API Wrapper layer and recreate the problem in the simplest possible example against the raw/pure DI REST API before engaging with the vendor's tech support team.

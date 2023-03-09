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
7. For testing and interactive usage, we use and recommend Jupyter Notebook, which is installed as part of Anaconda (https://www.anaconda.com/)
8. we highly recommend to reference the samples provided in this project (all files not matching deepinstinct*.py) for examples of how to import and use the API Wrapper as described above.

Notes/Disclaimer:
This repository is provided under GNU General Public License v3.0. This code is provided as a [hopefully] useful set of examples and base code to assist you with writing code to instrument your own custom logic against Deep Instinct REST APIs in both the management server (D-Appliance) and Agentless scanners, and also for education of the broader community on how to interact with RESTful APIs in general (not specific to any specific vendor). 

DEEP INSTINCT MAKES NO WARRANTIES OR REPRESENTATIONS REGARDING DEEP INSTINCT’S PROGRAMMING SCRIPTS. TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, DEEP INSTINCT DISCLAIMS ALL OTHER WARRANTIES, REPRESENTATIONS AND CONDITIONS, WHETHER EXPRESS, STATUTORY, OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE OR NON-INFRINGEMENT, AND ANY WARRANTIES ARISING OUT OF COURSE OF DEALING OR USAGE OF TRADE. DEEP INSTINCT’S PROGRAMMING SCRIPTS ARE PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, AND DEEP INSTINCT DISCLAIMS ALL OTHER WARRANTIES, EXPRESS, IMPLIED OR STATUTORY, INCLUDING ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.

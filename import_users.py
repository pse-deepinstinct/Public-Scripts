# Example of how to read a list of users from an Excel spreadsheet and bulk
# create them using the REST API.
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
import deepinstinct3 as di
import pandas

def main():

    #prompt for config parameters

    fqdn = input('Enter FQDN of DI Server, or press enter to accept the default [di-service.customers.deepinstinctweb.com]: ')
    if fqdn == '':
        fqdn = 'di-service.customers.deepinstinctweb.com'

    key = input('Enter API Key for DI Server: ')

    print("""
This script accepts input from a single sheet Excel workbook.

The first row of the input file must be column labels, which are cASE SeNSITIve.

The input file must contain the following 6 columns:
    username
    password
    first_name
    last_name
    email
    role

The 'role' column must contain one of these 6 values for each row:
    MASTER_ADMINISTRATOR
    ADMINISTRATOR
    IT_ADMIN
    SOC_ADMIN
    ACCOUNT_ADMINISTRATOR
    READ_ONLY

Column order is irrelevant.

Extra columns are OK and will be ignored.
    """)

    file_name = input('Enter name of file containing users to import, or press enter to accept the default [users.xlsx]: ')
    if file_name == '':
        file_name = 'users.xlsx'

    #run the import
    return run_user_import(fqdn=fqdn, key=key, file_name=file_name)

def run_user_import(fqdn, key, file_name):

    di.fqdn = fqdn
    di.key = key

    #read users to import from file on disk as Pandas dataframe
    user_list_df = pandas.read_excel(file_name)

    #replace any null values with empty string to avoid subsequent errors
    user_list_df.fillna('', inplace=True)

    #convert Pandas dataframe to Python dictionary
    user_list = user_list_df.to_dict('records')


    print('INFO: Successful read', len(user_list), 'records from', file_name)

    #iterate though the imported user list
    for user in user_list:
        di.create_user(username=user['username'], password=user['password'], first_name=user['first_name'], last_name=user['last_name'], email=user['email'], role=user['role'])

if __name__ == "__main__":
    main()

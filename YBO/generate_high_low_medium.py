
import pandas as pd
import requests
from requests_kerberos import HTTPKerberosAuth
headers = {'Content-type': 'application/json'}

path=r"C:\NAMAN\Share\YBO\Sent Test Plans\RPL-Hx Legacy BIOS 18-04-2023 (Only RPL data considered)\FIVC_BIOS_RPL-Hx update + RPL-Hx legacy_FV_Production.xlsx"
dataframes = pd.read_excel(path) 

dataframes.columns = [x.upper() for x in dataframes.columns]
df_length = len(dataframes.columns)                            #extract only column names
print("DF Length: {0}".format(df_length))

for j in range(len(dataframes)): 
            #if not pd.isna(dataframes.iloc[j, 0]):
            tcd_id = int(dataframes.at[j, "TCD_ID"])
            print("Current_TCD_ID = {0}".format(tcd_id))
            url = 'https://hsdes-api.intel.com/rest/article/' + str(tcd_id)
            response = requests.get(url, verify = False, auth = HTTPKerberosAuth(), headers = headers)	
            print("Response = {0}".format(response))
            print("Response code = {0}".format(response.status_code))
            if (response.status_code == 200):
                data_rows = response.json()['data']
                #print(data_rows)
                print("Valid response got... creating new columns")
                for row in data_rows:
                    
                    dataframes.at[j, 'Test_Complexity'] = row['central_firmware.test_case_definition.test_complexity']
                    dataframes.at[j, 'Test_Coverage_Level'] = row['central_firmware.test_case_definition.test_coverage_level']
                    
print(dataframes)
dataframes.to_excel(path)

import requests

from requests_kerberos import HTTPKerberosAuth
headers = {'Content-type': 'application/json'}
from requests.auth import HTTPBasicAuth
username="bchunch"
password="169e4733-c3fa-46f8-9d9d-c71d894c7a63"
          

tcd_id="16015632147"
url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(tcd_id)
print(tcd_id)
response1 = requests.get(url, verify = False, auth = HTTPBasicAuth(username,password), headers = headers)
if (response1.status_code == 200):
    data_rows = response1.json()['data']
    print("agarwal")
    for row in data_rows:
    #if response1.json().message:
        if "central_firmware.test_case_definition.test_coverage_level" in row.keys():
            print(row['test_case_definition.test_coverage_level']) 
        else:
            print("SORTED")
else:
    print(response1.status_code)   

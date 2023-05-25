import pandas as pd
import requests
from requests_kerberos import HTTPKerberosAuth
headers = {'Content-type': 'application/json'}
parent_tcd_id=14013184829
parent_tcd_id_url = 'https://hsdes-api.intel.com/rest/article/' + str(parent_tcd_id)
parent_tcd_id_response = requests.get(parent_tcd_id_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
if parent_tcd_id_response.status_code == 200:
    print(parent_tcd_id_response.json()['data'][0]['component'])
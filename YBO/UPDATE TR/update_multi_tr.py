import requests
from requests.auth import HTTPBasicAuth
from requests_kerberos import HTTPKerberosAuth
import csv
import json



headers = {'Content-type': 'application/json'}
username= "" #username required if using BasicAuth
password= "" #password required if using KerberosAuth

#-----csv file should have first column of the test result id--------------------#


def update_tr_multiple(csv_file, json_file):
    # Read the JSON file containing the reason value
    with open(json_file) as json_data_file:
        json_data = json.load(json_data_file)
    status_value = json_data["config"]["status"]
    reason_value = json_data["config"]["reason"]
    
    # Construct the payload for the PUT request
    payload = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                continue  # skip header row
            test_result_id = row[0]
            payload.append({
                "rowNum": i - 1,
                "id": int(test_result_id),
                "fieldValues": [
                    {
                        "status": status_value
                    },
                    {
                        "reason": reason_value
                    }
                ]
            })

    # Send the PUT request

    #request using basicAuth
    #put_url = 'https://hsdes-api.intel.com/rest/auth/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
    #resp = requests.put(url=put_url, json=payload, verify=False, auth=HTTPBasicAuth(username, password), headers=headers)

    #request using kerberosAuth
    put_url = 'https://hsdes-api.intel.com/rest/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
    resp = requests.put(url=put_url, json=payload, verify=False, auth=HTTPKerberosAuth(), headers=headers)
    
    if resp.status_code == 200:
        print(f"{len(payload)} test results updated successfully")
    else:
        print(f"Failed to update test results: {resp.status_code}")

#update the path of csv and json file accordingly
update_tr_multiple('C:/NAMAN/Share/YBO/UPDATE TR/test_results_id.csv', 'C:/NAMAN/Share/YBO/UPDATE TR/tr_reason_config.json')


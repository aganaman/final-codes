import requests
from requests.auth import HTTPBasicAuth


headers = {'Content-type': 'application/json'}

cid = 1
page_size = 50

start_at = 1
max_result = 10**5
base_url = 'https://hsdes-api.intel.com/rest/auth/query/execution/eql?max_results=' + str(max_result) + "&start_at=1"
username= "namanaga"
password= "57aef19b-d319-41f0-8851-ba38d2818f6e"

in_test_cycle ="bios.meteorlake.A0 PO Start.Client-BIOS.WW21_MTL_A0_PO_Phase2B"
in_config = "bios.meteorlake-MTL-P-A0_PO_Config_Entry"
in_planned_for = "RPL_S_Beta_HLK_BAT"
tc_ids = []
tcd_ids = []
tr_to_tc_mapping = {}
tc_to_tcd_mapping = {}

#generate tc id from subject==test_result and test-list==test_cycle 
def gen_tc_test_cycle():
    eql_test_case_definitions = "\"eql\":\"select id, title, parent_id, submitted_date where " \
                        "tenant='central_firmware' and subject='test_result' and test_result.test_cycle contains '{0}' and test_result.configuration contains '{1}'" \
                        "\"".format(in_test_cycle,in_config)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
    resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
    if resp.status_code == 200:
        test_results_data = resp.json()['data']
        #print(test_results_data)
    else:
        print(resp.status_code)

    for single_tr_data in test_results_data:
        tc_ids.append(single_tr_data['parent_id'])
        tr_to_tc_mapping[single_tr_data['id']] = single_tr_data['parent_id']

    print("len of tc_ids: ", len(tc_ids))
    #for tc_id in tc_ids:
    #    tcd_ids.append(gen_tcd_test_cycle(tc_id))

    #print("len of tcd_ids: ", len(tcd_ids))
    gen_tcd_test_cycle(tc_ids)

#generate tcd id from subject==test_case and test-list==test_cycle
def gen_tcd_test_cycle(tc_ids):
    eql_test_case_definitions = "\"eql\":\"select id, title, parent_id, submitted_date where " \
                    "tenant='central_firmware' and subject='test_case' and test_case.test_cycle contains '{0}' and central_firmware.test_case.configuration contains '{1}' and id IN ({2})" \
                    "\"".format(in_test_cycle, in_config, ",".join(tc_ids))


    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
    resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
    if resp.status_code == 200:
        test_case_data = resp.json()['data']
        #print(test_results_data)
    else:
        print(resp.status_code)
    #print(test_case_data)

    for single_tc_data in test_case_data:
        tcd_ids.append(single_tc_data['parent_id'])
        tc_to_tcd_mapping[single_tc_data['id']] = single_tc_data['parent_id']

    #tc_to_tcd_mapping[test_case_data[0]['id']] = test_case_data[0]['parent_id']
    #return test_case_data[0]['parent_id']
    #return tcd_ids
    print(tcd_ids)
    print("len of tcd_ids: ", len(tcd_ids))
    

#gen_tc_test_cycle()


#generate tcds from subject == test_case and test_list==test plan:
def gen_tcds_test_plan():
    eql_test_case_definitions = "\"eql\":\"select id, title, parent_id, submitted_date where " \
                        "tenant='central_firmware' and subject='test_case' and central_firmware.test_case.planned_for contains '{0}' and central_firmware.test_case.configuration contains '{1}'" \
                        "\"".format(in_planned_for,in_config)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
    resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
    if resp.status_code == 200:
        test_case_data = resp.json()['data']
        #print(test_results_data)
    else:
        print(resp.status_code)

    for single_tc_data in test_case_data:
        tc_ids.append(single_tc_data['id'])
        tcd_ids.append(single_tc_data['parent_id'])
        tc_to_tcd_mapping[single_tc_data['id']] = single_tc_data['parent_id']
    
    print(len(tcd_ids))

#gen_tcds_test_plan()
test_result_id = "16016694547"
#update tr of optimized tcs:

import json
import requests

def update_tr(test_result_id):
    # Construct the URL
    put_url = f'https://hsdes-api.intel.com/rest/auth/article/{test_result_id}?fetch=false&debug=false'

    # Construct the payload
    payload = {
        "tenant": "central_firmware",
        "subject": "test_result",
        "fieldValues": [
            {
                "status": "blocked"
            },
            {
                "reason": "other"
            }
        ]
    }

    # Send the PUT request
    resp = requests.put(url=put_url, json=payload, verify=False, auth=HTTPBasicAuth(username, password), headers=headers)
    if resp.status_code == 200:
        print(f"Test result {test_result_id} updated successfully")
    else:
        print(f"Failed to update test result {test_result_id}: {resp.status_code}")

update_tr("15012842896")


import csv
import json
import requests

def update_tr_multiple(csv_file, json_file):
    # Read the JSON file containing the reason value
    with open(json_file) as json_data_file:
        json_data = json.load(json_data_file)
    reason_value = json_data["config"]["reason"]
    status_value = json_data["config"]['status']
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
                "rev": 0,  # set to 0 to force update regardless of version
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
    put_url = 'https://hsdes-api.intel.com/rest/auth/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
    resp = requests.put(url=put_url, json=payload, verify=False, auth=HTTPBasicAuth(username, password), headers=headers)

    if resp.status_code == 200:
        print(f"{len(payload)} test results updated successfully")
    else:
        print(f"Failed to update test results: {resp.status_code}")

#update_tr_multiple('C:/NAMAN/Share/YBO/UPDATE TR/test_results_id.csv', 'C:/NAMAN/Share/YBO/UPDATE TR/tr_reason_config.json')

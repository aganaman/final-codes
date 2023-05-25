import requests
from requests.auth import HTTPBasicAuth
from requests_kerberos import HTTPKerberosAuth
import json

headers = {'Content-type': 'application/json'}

cid = 1
page_size = 50

start_at = 1
max_result = 10**6

#---------------------------------------if using BasicAuth-------------------------------------------------------------------------------

#base_url = 'https://hsdes-api-pre.intel.com/rest/auth/query/execution/eql?max_results=' + str(max_result) + "&start_at=1"
#post_url = 'https://hsdes-api-pre.intel.com/rest/auth/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
#username= ""
#password= ""

#---------------------------------------------------------------------------------------------------------------------------------------------

#---------------------------------------if using kerberosAuth------------------------------------------------------------------------------------

base_url = 'https://hsdes-api-pre.intel.com/rest/query/execution/eql?max_results=' + str(max_result) + "&start_at=1"
post_url = 'https://hsdes-api-pre.intel.com/rest/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'

#---------------------------------------------------------------------------------------------------------------------------------------------

tc_ids =[]
tc_to_tc_title_mapping = {}
tc_to_release_aff = {}

def create_trs(tc_ids, tc_to_tc_title_mapping, status_value, reason_value, link_type, tc_to_release_aff, owner):
    max_chunk_size = 25 # Set the maximum number of test cases to include in each request
    num_chunks = (len(tc_ids) + max_chunk_size - 1) // max_chunk_size # Calculate the number of chunks needed
    
    for chunk_num in range(num_chunks):
        start_idx = chunk_num * max_chunk_size
        end_idx = min(start_idx + max_chunk_size, len(tc_ids))
        chunk_tc_ids = tc_ids[start_idx:end_idx]
        chunk_payload = []
        print(chunk_tc_ids)
        print(reason_value)
        for i in range(len(chunk_tc_ids)):
            parent_id = chunk_tc_ids[i]
            title = tc_to_tc_title_mapping[chunk_tc_ids[i]] + " [TC ID" + chunk_tc_ids[i] + "]"
            release_aff = tc_to_release_aff[chunk_tc_ids[i]]
            chunk_payload.append({
                "rowNum": i,
                "fieldValues": [
                    {
                        "title": title
                    },
                    {
                        "parent_id": parent_id
                    },
                    {
                        "owner": owner
                    },
                    {
                        "link_type": link_type
                    },
                    {
                        "status": status_value
                    },
                    {
                        "reason": reason_value
                    },
                    {
                        "release":release_aff
                    },
                    {
                        "test_result.test_cycle": "bios.2lm.A0 Execution.Client-BIOS.949 Test"
                    },
                    {
                        "test_result.configuration":"bios.alderlake-h_fpga"
                    }
                ]
            })
        #print(chunk_payload)
        #use below resp if using basicauth
        #resp = requests.post(url=post_url, json=chunk_payload, verify=False, auth=HTTPBasicAuth(username, password), headers=headers)
        resp = requests.post(url=post_url, json=chunk_payload, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        if resp.status_code == 200:
            print(f"{len(chunk_payload)} test results updated successfully")
        else:
            print(f"Failed to update test results: {resp.status_code}")



def fetch_tc_id_test_cycle(test_cycle_name,config):
    eql_test_case_definitions = "\"eql\":\"select id, title, release_affected, submitted_date where " \
                        "tenant='central_firmware' and subject='test_case' and test_case.test_cycle contains '{0}' and central_firmware.test_case.configuration contains '{1}'" \
                        "\"".format(test_cycle_name,config)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
    #use below resp if using basicauth
    #resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
    resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPKerberosAuth(), headers = headers)
    if resp.status_code == 200:
        test_results_data = resp.json()['data']
        #print(test_results_data)
    else:
        print(resp.status_code)

    for single_tr_data in test_results_data:
        tc_ids.append(single_tr_data['id'])
        tc_to_tc_title_mapping[single_tr_data['id']] = single_tr_data['title']
        tc_to_release_aff[single_tr_data['id']] = single_tr_data['release_affected']
    
    print(len(tc_ids))
    tc_ids.sort()
    return tc_ids, tc_to_tc_title_mapping, tc_to_release_aff

if __name__ == "__main__":
    with open("tr_config.json") as json_data_file:
        json_data = json.load(json_data_file)
    test_cycle_name = json_data["data"]["test_cycle"]
    config = json_data["data"]["config"]
    status_value = json_data["data"]["status"]
    reason_value = json_data["data"]["reason"]
    link_type = json_data["data"]["link_type"]
    owner = json_data["data"]["owner"]

    tc_ids, tc_to_tc_title_mapping, tc_to_release_aff  = fetch_tc_id_test_cycle(test_cycle_name,config)
    
    create_trs(tc_ids, tc_to_tc_title_mapping, status_value, reason_value, link_type, tc_to_release_aff, owner)
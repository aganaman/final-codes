import requests
from requests.auth import HTTPBasicAuth
from requests_kerberos import HTTPKerberosAuth
import json
import csv
import argparse
from datetime import datetime



headers = {'Content-type': 'application/json'}

cid = 1
page_size = 50

start_at = 1
max_result = 10**6

#for BAsic Auth
#base_url = 'https://hsdes-api.intel.com/rest/auth/query/execution/eql?max_results=' + str(max_result) + "&start_at=1"
username= ""
password= ""

#for kerberos auth
base_url = 'https://hsdes-api.intel.com/rest/query/execution/eql?max_results=' + str(max_result) + "&start_at=1"



#tc_ids = ["1308241869","1308241871","1308241877","1308510911","1308510912","1308242525"]

#function to create TR
def create_tr_multiple(not_have_tr, status_value, reason_value, link_type, owner, test_cycle_name, tc_id_to_title, release, reason_other, id_list):
    max_chunk_size = 25 # Set the maximum number of test cases to include in each request
    num_chunks = (len(not_have_tr) + max_chunk_size - 1) // max_chunk_size # Calculate the number of chunks needed
    
    for chunk_num in range(num_chunks):
        start_idx = chunk_num * max_chunk_size
        end_idx = min(start_idx + max_chunk_size, len(not_have_tr))
        chunk_tc_ids = not_have_tr[start_idx:end_idx]
        chunk_payload = []
        #print(chunk_tc_ids)
        #print(reason_value)
        for i in range(len(chunk_tc_ids)):
            parent_id = chunk_tc_ids[i]
            title = tc_id_to_title[chunk_tc_ids[i]][0] + " [TC ID" + chunk_tc_ids[i] + "]"
            release_aff = release
            configuration = tc_id_to_title[chunk_tc_ids[i]][1]
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
                        "test_result.test_cycle": test_cycle_name
                    },
                    {
                        "test_result.configuration": configuration
                    },
                    {
                        "reason_other": reason_other
                    }
                ]
            })
        #print(chunk_payload)
        #use below resp if using basicauth
        #post_url = 'https://hsdes-api.intel.com/rest/auth/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
        #resp = requests.post(url=post_url, json=chunk_payload, verify=False, auth=HTTPBasicAuth(username, password), headers=headers)
        #if using kerberosauth
        post_url = 'https://hsdes-api.intel.com/rest/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
        resp = requests.post(url=post_url, json=chunk_payload, verify=False, auth=HTTPKerberosAuth(), headers=headers)
        if resp.status_code == 200:
            print(f"{len(chunk_payload)} test results created successfully")
            json_object = resp.json()
            #print(json_object)

            for key in json_object['details']:
                id_list.append(json_object['details'][key]['id'])
            #print(id_list)
        else:
            print(f"Failed to update test results: {resp.status_code}")
    
    return id_list


#this function will set the closed_date field if newly created TR's
def update_new_tr(id_list):
    max_chunk_size = 25 # Set the maximum number of test cases to include in each request
    num_chunks = (len(id_list) + max_chunk_size - 1) // max_chunk_size # Calculate the number of chunks needed
    now = datetime.now()
    #print(now)
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    #print(now_str)
    for chunk_num in range(num_chunks):
        start_idx = chunk_num * max_chunk_size
        end_idx = min(start_idx + max_chunk_size, len(id_list))
        chunk_tc_ids = id_list[start_idx:end_idx]
        chunk_payload = []
        print(chunk_tc_ids)
        for i in range(len(chunk_tc_ids)):
            test_result_id = chunk_tc_ids[i]
            chunk_payload.append({
                "rowNum": i,
                "id": int(test_result_id),
                "fieldValues": [
                    {
                        "closed_date": now_str
                    }
                ]
            })
        #request using KerberosAuth
        put_url = 'https://hsdes-api.intel.com/rest/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
        resp = requests.put(url=put_url, json=chunk_payload, verify=False, auth=HTTPKerberosAuth(), headers=headers)

        #request using basicAuth
        #put_url = 'https://hsdes-api.intel.com/rest/auth/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
        #resp = requests.put(url=put_url, json=chunk_payload, verify=False, auth=HTTPBasicAuth(username,password), headers=headers)
        
        
        if resp.status_code == 200:
            print(f"{len(chunk_payload)} new created test results updated successfully")
        else:
            print(f"Failed to update test results: {resp.status_code}")


#function to update the existing valid TR for a TC
def update_tr_multiple(have_tr, status_value, reason_value, owner, reason_other):
    # Construct the payload for the PUT request
    max_chunk_size = 25 # Set the maximum number of test cases to include in each request
    num_chunks = (len(have_tr) + max_chunk_size - 1) // max_chunk_size # Calculate the number of chunks needed
    now = datetime.now()
    #print(now)
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    #print(now_str)
    for chunk_num in range(num_chunks):
        start_idx = chunk_num * max_chunk_size
        end_idx = min(start_idx + max_chunk_size, len(have_tr))
        chunk_tc_ids = have_tr[start_idx:end_idx]
        chunk_payload = []
        print(chunk_tc_ids)
        print(reason_value)
        for i in range(len(chunk_tc_ids)):
            test_result_id = chunk_tc_ids[i]
            chunk_payload.append({
                "rowNum": i,
                "id": int(test_result_id),
                "fieldValues": [
                    {
                        "status": status_value
                    },
                    {
                        "reason": reason_value
                    },
                    {
                        "owner": owner
                    },
                    {
                        "reason_other": reason_other
                    },
                    {
                        "closed_date": now_str
                    }
                ]
            })
        
        # Send the PUT request

        #request using KerberosAuth
        put_url = 'https://hsdes-api.intel.com/rest/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
        resp = requests.put(url=put_url, json=chunk_payload, verify=False, auth=HTTPKerberosAuth(), headers=headers)

        #request using basicAuth
        #put_url = 'https://hsdes-api.intel.com/rest/auth/article/bulk/sync/central_firmware/test_result?fetch=false&send_mail=false'
        #resp = requests.put(url=put_url, json=chunk_payload, verify=False, auth=HTTPBasicAuth(username,password), headers=headers)
        
        
        if resp.status_code == 200:
            print(f"{len(chunk_payload)} test results updated successfully")
        else:
            print(f"Failed to update test results: {resp.status_code}")


#function to find if tr exists for a tc
def fetch_tc_id_tr_id(tc_ids, test_cycle_name, tc_id_to_title):
    have_tr=[] #list containing existing tr_id with same test cycle name and config] 
    not_have_tr=[] #list conatining tc_id which don't have valid tr
    parent_latest_child = {} #dictionary to maintain latest valid tr for each tc if exists
    
    print("------------------------------------------in fetch tc tr id-------------------------------------------------------------------")
    print(tc_ids)

    for i in range(len(tc_ids)):
        test_case_id = tc_ids[i]
        configuration = tc_id_to_title[tc_ids[i]][1]
        #print(test_case_id,configuration)
        eql_test_case_definitions = "\"eql\":\"select id, title, release, submitted_date where " \
                            "tenant='central_firmware' and subject='test_result' and test_result.test_cycle contains '{0}' and test_result.configuration = '{1}' and parent_id = '{2}'" \
                            "\"".format(test_cycle_name,configuration,test_case_id)

        payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
        #use below resp if using basicauth
        #resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username,password), headers = headers)
        #use below if using KerberosAuth
        resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPKerberosAuth(), headers = headers)
        if resp.status_code == 200:
            test_results_data = resp.json()['data']
            #print(test_results_data)
        else:
            print(resp.status_code)

        #print(test_results_data)

        for record in test_results_data:
            if record['parent_id'] not in parent_latest_child:
                parent_latest_child[record['parent_id']] = record
            else:
                if record['submitted_date'] > parent_latest_child[record['parent_id']]['submitted_date']:
                    parent_latest_child[record['parent_id']] = record

    #print("---------------------------------parent-latest-child---------------------------------")
    #print(parent_latest_child)
    #print(parent_latest_child.keys())
    for i in parent_latest_child.keys():
        have_tr.append(parent_latest_child[i]["id"]) #list containing lastest tr id of a tc
    
    for i in tc_ids:
        if i not in parent_latest_child.keys():
            not_have_tr.append(i)  #list containing tc id having no tr
    
    print("\n")
    print("------------------------------have tr----------------------------------------")
    print(have_tr)
    print("------------------------------not have tr----------------------------------------")
    print(not_have_tr)
    return have_tr, not_have_tr


#function to fetch data from csv file provided in the given path
#Note: Strictly maintain the order in csv column-1: TC_ID, column-2: TC_Title, column-3: Configuration
def read_tc_ids(csv_file_path):
    # Open the CSV file and read its contents
    with open(csv_file_path, encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        
        # Skip the first row
        next(csv_reader)
        
        for row in csv_reader:
            # Extract the 'TC_ID' and 'TC_Title' values from the row
            tc_id = row[0]
            tc_title = row[1]
            tc_config = row[2]
            
            # Add the values to the dictionary
            tc_id_to_title[tc_id] = [tc_title,tc_config]

    # Print the dictionary
    print("---------------------------TC_ID_TO_TITLE DICTIONARY-----------------------------------------")
    print(tc_id_to_title)
    tc_ids = list(tc_id_to_title.keys())
    print("---------------------------TC_IDS---------------------------------------------------")
    print(tc_ids)
    return tc_ids,tc_id_to_title


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', help="csv file path containing tc_id, tc_tile and configuration")
    parser.add_argument('-tc', help="Name of test cycle")
    parser.add_argument('-sv', help="value of status field(complete, blocked, etc)")
    parser.add_argument('-rv', help="value of reason field(pass, fail, optimized, etc)")
    parser.add_argument('-rl', help="Name of release affected (bios.raptorlake, etc)")
    parser.add_argument('-lt', help="value of link type (parent-child)")
    parser.add_argument('-o', help="name of owner(eg: namanaga)")
    parser.add_argument('-ro', help="Value of reason.other when status.reason==blocked.other (eg: manual_result)", required=False)
    args = parser.parse_args()

    tc_ids = [] #LIST OF TC_ID to be fetched from csv
    have_tr = [] #list containing existing tr_id with same test cycle name and config
    not_have_tr = [] #list conatining tc_id which don't have valid tr
    tc_id_to_title={} #dictionary to maintain latest valid tr for each tc if exists
    id_list = [] #list to contain tr_id of new created tr
    
    path = args.p
    test_cycle_name = args.tc
    status_value = args.sv
    reason_value = args.rv
    release = args.rl
    link_type = args.lt
    owner = args.o
    reason_other = args.ro
        
    tc_ids, tc_id_to_title = read_tc_ids(path)
    #tc_ids =['1308975227', '1308975229', '1605780546']
    have_tr, not_have_tr = fetch_tc_id_tr_id(tc_ids,test_cycle_name,tc_id_to_title)
    if len(have_tr) > 0:
        print("--------------------------calling update_tr_multiple----------------------------------------------------")
        update_tr_multiple(have_tr, status_value, reason_value, owner, reason_other)
    if len(not_have_tr) > 0:
        print("---------------------------calling create_tr_multiple---------------------------------------------------")
        id_list = create_tr_multiple(not_have_tr, status_value, reason_value, link_type, owner, test_cycle_name, tc_id_to_title, release, reason_other, id_list)
    if len(id_list) > 0: 
        print("----------------------------calling update new created tr--------------------------------------------------")
        update_new_tr(id_list)
    print("--------------------------------Script Ending---------------------------------")
    #sample python command
    #py script1_prod_cmd.py -p C:\NAMAN\Share\Create_Update_TR_using_TC\Book5.csv -tc "bios.a21.A0 PO Exit.Client-BIOS.bob_test" -sv "complete" -rv "fail" -rl "bios.alderlake" -lt "parent-child" -o "namanaga" 
    #py script1_prod_cmd.py -p C:\NAMAN\Share\Create_Update_TR_using_TC\Book5.csv -tc "bios.a21.A0 PO Exit.Client-BIOS.bob_test" -sv "blocked" -rv "other" -rl "bios.alderlake" -lt "parent-child" -o "namanaga" -ro "manual_result"
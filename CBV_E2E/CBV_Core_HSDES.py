import requests
import re
import xlrd
import xlwt
import json
import sys
import os
from xlwt import Workbook
from requests_kerberos import HTTPKerberosAuth
import urllib3
import time
from requests.auth import HTTPBasicAuth
import getpass
import math
import pandas
import datetime
import re
import pandas as pd
import logging

# MaxRecordsPerPage = 50
# if len(sys.argv) != 7:
#        sys.exit("USAGE: python3 hsd_commit_cmd.py {Config file} {git log} {SHA_ID1} {SHA_ID2} {username} {HSDES_token_password}")

# username = sys.argv[5]
# password = sys.argv[6]



""" Getting TCD data from ISE/Bugs """
def get_tcd(config_file_path, git_log_path, sha_id_1, sha_id_2):

    k = []

    with open(config_file_path) as config_file:
        data = json.load(config_file)

    print("Config File Data: ")
    print(data)
    for key, value in data.items():
        k.append(value)
    username = data["username"]
    password = data["password"]
    print("Username: {0}".format(username))
    print("Password: {0}".format(password))

    final = [[] for i in range(len(k))]

    hsd_id = []

    hsd_sub = [] 
    hsd_ten = []
    hsd_index = []
    hsd_match_id = []
    hsd_match_sub = []
    hsd_match_ten = []
    lines = []
    lines_loop = []
    hsd_list = []
    final_hsd = []
    final_data = {}

    # parsing gitlog

    sub_str = 'Hsd-es-id'
    author = 'Author:'
    review_links = 'Reviewed-on:'

    str1 = sha_id_1
    str2 = sha_id_2


    # Reads git log file
    with open(git_log_path, encoding = 'utf-8') as infile:
        for line in infile:
            lines.append(line)

    # finding index of sha-id 1 and sha-id 2 (index1 and index2)
    indices = [i for i, s in enumerate(lines) if author in s]
    index1 = lines.index('commit '+ str1 + '\n')
    index2 = lines.index('commit '+ str2 + '\n')

    # Takes care of the scenario where second commit id (sha-id 2) is not actual last id in the git log file
    if ((indices[-1])!= indices[indices.index(index2+1)]):
        index2 = indices[indices.index(index2+1) + 1]
    else:
        index2 = len(lines)

    # Filters data only from index1 and index2 for use
    for i in range(index1, index2):
        lines_loop.append(lines[i])
            
    # Gets the lines where hsdes-id is there
    res = [x for x in lines_loop if re.search(sub_str, x)]
    res_1 = [x for x in lines_loop if re.search(review_links, x)]

    res_ = []

    for i in range(len(res)):
        res_.append(re.sub(r'(?<=[:,])(?=[^\s])', r' ', res[i]))
    for j in range(len(res_)):
        find_hsd = re.findall(r'\d+',res_[j] )
        final_hsd.append(find_hsd)

    final_list_hsd = [val for sublist in final_hsd for val in sublist]

    list_hsd = list(set(final_list_hsd))
    print("List of HSD IDs from git log:")
    print(list_hsd)
    #print(len(list_hsd))


    # this is to ignore the ssl insecure warning as we are passing in 'verify=false'
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


    t = [] 
    final_tcd_data = []
    headers = { 'Content-type': 'application/json' }
    #Replace the ID here with some article ID
    for i in range(len(list_hsd)):
        print("-----------------------------------------------------------------------------------------------")
        print("Current execution HSD ID from git log: {0}".format(list_hsd[i]))
        print("-----------------------------------------------------------------------------------------------")
        # URL for BasicAuth()
        url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(list_hsd[i])
        # URL for KerberosAuth()
        # url = 'https://hsdes-api.intel.com/rest/article/' + str(list_hsd[i])
        # print(url)
        
        response = requests.get(url, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
        # response = requests.get(url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
        if response.status_code == 200:
            print("Got valid response 200 for current execution HSD ID.")
            result = response.json()
            print("Response of current execution HSD ID")
            print(result)
            for j in range(len(final)):
                if 'data' in result:
                    try:
                        final[j].append(result['data'][0][k[j]])
                    except KeyError:
                        final[j].append('N/A')
                else:
                    final[j].append('ACCESS DENIED')
            
            if 'data' in result:
                if result['data'][0]['subject'] == 'integration_step_event':
                    final_data[str(list_hsd[i])] = ["ISE"]
                    print("**********************************************************************************")
                    print("Inside ISE - {0}".format(result['data'][0]['id']))
                    print("**********************************************************************************")
                    if 'parent_id' in result['data'][0]:
                        parent_id = response.json().get('data')[0]['parent_id']
                        print("Parent (Feature) ID found - {0}".format(parent_id))
                        # This is a feature URL 
                        # Feature URL for BasicAuth()
                        feature_url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(parent_id)
                        # Feature URL for KerberosAuth()
                        # feature_url = 'https://hsdes-api.intel.com/rest/article/' + str(parent_id)
                        print("Requesting parent (feature) article...")
                        resp = requests.get(feature_url, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
                        # resp = requests.get(feature_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
                        print("Parent (Feature) request completed.")
                        if resp.json()["data"][0]["subject"] == "feature":
                            if resp.status_code == 200:
                                print("Response of Feature (i.e. parent of ISE): ")
                                print(resp.json())
                                if "data" in resp.json():
                                    if "central_firmware.feature.val_assessment_reason" in resp.json()["data"][0]:
                                        if resp.json()["data"][0]["central_firmware.feature.val_assessment_reason"] == "testable_requirement":
                                            print("Preparing Parent (Feature) Links URL...")
                                            # Feature Links URL for BasicAuth()
                                            feature_links_request_url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(parent_id) + '/links'
                                            # Feature Links URL for KerberosAuth()
                                            # feature_links_request_url = 'https://hsdes-api.intel.com/rest/article/' + str(parent_id) + '/links'
                                            print("Requesting for parent (feature) links...")
                                            # feature_links_response = requests.get(feature_links_request_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
                                            feature_links_response = requests.get(feature_links_request_url, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
                                            print("Request to parent (feature) links complete.")
                                            print("Parent (Feature) links response status code {0} found.".format(feature_links_response.status_code))
                                            if feature_links_response.status_code == 200:
                                                print("ISE's parent feature links response")
                                                print(feature_links_response.json())

                                                tcd_data = [x for x in feature_links_response.json()["responses"] if x["subject"] == "test_case_definition"]
                                                print("TCD Data from ISE's parent feature links")
                                                print(tcd_data)
                                                for m in tcd_data:
                                                    s = '=HYPERLINK(\"https://hsdes.intel.com/appstore/article/#/{0}\", \"{1}\")'.format(m['id'], m['id'])
                                                    final_tcd_data.append([s, m['title']])
                                                    final_data[str(list_hsd[i])].append([s, m['title']])
                                            else:
                                                print("ISE's parent (feature) links response not valid. Getting response {0}".format(feature_links_response.status_code))
                                        else:
                                            print("ISE's parent (feature) is not 'testable_requirement', skipping...")
                                else:
                                    print("'Data' not found in ISE's parent feature response.")
                            else:
                                print("ISE's parent (feature) reponse is not valid. Getting response {0}.".format(resp.status_code))
                        else:
                            print("ISE's parent is not having subject as 'feature'. Feature not found as ISE's parent.")
                    else:
                        print("Parent ID not found in ISE response.")

                elif result['data'][0]['subject'] == 'bug':
                    final_data[str(list_hsd[i])] = ["Bug"]
                    print("**********************************************************************************")
                    print("Inside Bug - {0}".format(result['data'][0]['id']))
                    print("**********************************************************************************")

                    # Finding TCDs from tets_case_id field of bug

                    if ('client_platf.bug.test_case_id' in result['data'][0]) or ('central_firmware.bug.test_case_id' in result['data'][0]):
                        print("Checking test_case_id field for TCDs...")
                        if 'client_platf.bug.test_case_id' in result['data'][0]:
                            bug_test_case_id_field_data = result['data'][0]['client_platf.bug.test_case_id']
                        elif 'central_firmware.bug.test_case_id' in result['data'][0]:
                            bug_test_case_id_field_data = result['data'][0]['central_firmware.bug.test_case_id']
                        if bug_test_case_id_field_data not in [None, "", " "]:
                            bug_test_case_id_field_data = bug_test_case_id_field_data.split(",")
                            bug_test_case_id_field_data = [str(z.strip()) for z in bug_test_case_id_field_data]
                            for bug_tc_id in bug_test_case_id_field_data:
                                print("ID inside Bug's test_case_id field: {0}".format(bug_tc_id))
                                if bug_tc_id != "":
                                    # Bug Test ID field URL for BasicAuth()
                                    bug_test_case_id_field_url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(bug_tc_id)
                                    # Bug Test ID field URL for KerberosAuth()
                                    # bug_test_case_id_field_url = 'https://hsdes-api.intel.com/rest/article/' + str(bug_tc_id)
                                    print("Requesting for article from bug's test_case_id field...")
                                    bug_tc_id_response = requests.get(bug_test_case_id_field_url, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
                                    # bug_tc_id_response = requests.get(bug_test_case_id_field_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
                                    print("Request for article from bug's test_case_id field complete.")
                                    if bug_tc_id_response.status_code == 200:
                                        print("Response 200 received for the article id inside bug's test_case_id field.")
                                        if bug_tc_id_response.json()['data'][0]['subject'] == 'test_case_definition':
                                            print("Article inside bug's test_case_id field is a valid TCD. Adding to final list.")
                                            s = '=HYPERLINK(\"https://hsdes.intel.com/appstore/article/#/{0}\", \"{1}\")'.format(bug_tc_id_response.json()['data'][0]['id'], bug_tc_id_response.json()['data'][0]['id'])
                                            final_tcd_data.append([s, bug_tc_id_response.json()['data'][0]['title']])
                                            final_data[str(list_hsd[i])].append([s, bug_tc_id_response.json()['data'][0]['title']])
                                    else:
                                        print("Bug TCD ID from test_case_id field - {0} response not valid.".format(bug_tc_id))
                                else:
                                    print("Bug TC ID from test_case_id is not valid.")
                        
                    # Finding links in Bug article

                    print("Preparing Bug Links URL...")
                    # Bug Links URL for BasicAuth()
                    bug_links_request_url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(result["data"][0]["id"]) + '/links'
                    # Bug Links URL for KerberosAuth()
                    # bug_links_request_url = 'https://hsdes-api.intel.com/rest/article/' + str(result["data"][0]["id"]) + '/links'
                    print("Requesting for Bug links...")
                    # bug_links_response = requests.get(bug_links_request_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
                    bug_links_response = requests.get(bug_links_request_url, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
                    print("Request to bug links complete.")
                    print("Bug links response status code {0} found.".format(bug_links_response.status_code))
                    if bug_links_response.status_code == 200:
                        print("Bug links response: ")
                        print(bug_links_response.json())
                        tr_data = [x for x in bug_links_response.json()["responses"] if x["subject"] == "test_result"]
                        print("TR Data from links of bug: ")
                        print(tr_data)
                        for m in tr_data:
                            print("Checking the TCD for TR {0}...".format(m["id"]))
                            # Test Result URL for BasicAuth()
                            test_result_url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(m["id"])
                            # Test Result URL for KerberosAuth()
                            # test_result_url = 'https://hsdes-api.intel.com/rest/article/' + str(m["id"])
                            print("Requesting for test_result article with ID: {0} from links of bug...".format(m["id"]))
                            test_result_response = requests.get(test_result_url, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
                            # test_result_response = requests.get(test_result_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
                            print("Request for test_result article with ID: {0} from links of bug is complete.",format(m["id"]))
                            if test_result_response.status_code == 200:
                                if 'parent_id' in test_result_response.json()['data'][0]:
                                    parent_tc_id = test_result_response.json().get('data')[0]['parent_id']
                                    print("Test Result's parent (Test Case) found. ID: {0}".format(parent_tc_id))
                                    # Parent TC URL for BasicAuth()
                                    parent_tc_id_url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(parent_tc_id)
                                    # Parent TC URL for KerberosAuth()
                                    # parent_tc_id_url = 'https://hsdes-api.intel.com/rest/article/' + str(parent_tc_id)
                                    print("Requesting for test result's parent test case: {0}".format(parent_tc_id))
                                    parent_tc_id_response = requests.get(parent_tc_id_url, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
                                    # parent_tc_id_response = requests.get(parent_tc_id_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
                                    print("Request for test result's parent test case with ID: {0} is complete.".format(parent_tc_id))
                                    if parent_tc_id_response.status_code == 200:
                                        if 'parent_id' in parent_tc_id_response.json()['data'][0]:
                                            parent_tcd_id = parent_tc_id_response.json().get('data')[0]['parent_id']
                                            print("Test Case's parent (Test Case Definition) found. ID: {0}".format(parent_tcd_id))
                                            # Parent TCD URL for BasicAuth()
                                            parent_tcd_id_url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(parent_tcd_id)
                                            # Parent TCD URL for KerberosAuth()
                                            # parent_tcd_id_url = 'https://hsdes-api.intel.com/rest/article/' + str(parent_tcd_id)
                                            print("Requesting for test case's parent test case definition: {0}".format(parent_tcd_id))
                                            parent_tcd_id_response = requests.get(parent_tcd_id_url, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
                                            # parent_tcd_id_response = requests.get(parent_tcd_id_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
                                            print("Request for test case's parent test case definition with ID: {0} is complete.".format(parent_tcd_id))
                                            if parent_tcd_id_response.status_code == 200:
                                                if parent_tcd_id_response.json()['data'][0]['subject'] == 'test_case_definition':
                                                    print("Valid test case definition: {0} found for given test result: {1} and test case: {2}. Adding to final list.".format(parent_tcd_id, m["id"], parent_tc_id))
                                                    s = '=HYPERLINK(\"https://hsdes.intel.com/appstore/article/#/{0}\", \"{1}\")'.format(parent_tcd_id_response.json()['data'][0]['id'], parent_tcd_id_response.json()['data'][0]['id'])
                                                    final_tcd_data.append([s, parent_tcd_id_response.json()['data'][0]['title']])
                                                    final_data[str(list_hsd[i])].append([s, parent_tcd_id_response.json()['data'][0]['title']])
                                            else:
                                                print("Test case's parent - TCD response not valid. Getting response {0}".format(parent_tcd_id_response.status_code))
                                    else:
                                        print("Test result's parent - Test case response not valid. Response {0} received.".format(parent_tc_id_response.status_code))   
                            else:
                                print("Test Result Call for ID - {0} response not valid. Getting response {1}".format(bug_tc_id, test_result_response.status_code))
                    else:
                        print("Bug links response not valid. Getting response {0}".format(feature_links_response.status_code))
                else:
                    print("Given HSD ID in git log is neither ISE nor Bug.")
                    print("Given HSD ID {0} is {1}. Skipping...".format(list_hsd[i], result['data'][0]['subject']))
            else:
                print("'data' part is not there in the result for current execution HSD ID {0}".format(list_hsd[i]))
        else:
            print("Invalid response for current execution HSD ID: {0}. Getting response {1}".format(list_hsd[i], response.status_code))


    # Handling duplicates
    final_tcd_data_unique = []
    for element in final_tcd_data:
        if element not in final_tcd_data_unique:
            final_tcd_data_unique.append(element)

    final_tcd_data_dict = {}
    for element in final_tcd_data_unique:
        final_tcd_data_dict[element[0]] = element[1]

    for key, value in final_data.items():
        temp_value = []
        for element in value:
            if element not in temp_value:
                temp_value.append(element)
        final_data[key] = temp_value

    df = pd.DataFrame(final_tcd_data_unique, columns = ["Test_Case_Definition_ID", "Test_Case_Definition_Title",])
    df.to_excel("output.xlsx", index=False) 

    print("Final TCD Data List ([[id, title], [id, title], ... [id, title]])")
    print(final_tcd_data_unique)
    print("Final Data Dictionary having TCD Data as well as info about corresponding ISE/Bug")
    print(final_data)
    print("Final Data Dictionary in user friendly format: ")
    for key, value in final_data.items():
        print("-----------------------------------------------------------------------------")
        print(key)
        for i in value:
            print(i)
    print("Final TCD Data Dictionary: ")
    print(final_tcd_data_dict)

    return final_tcd_data_dict


def main():

    final_tcd_data_dict = get_tcd("Config.JSON", "test.txt", "db5591d62ff28f8248959198247a83005f429c9c", "4ca286db6546ad8f6e79844433c4e23cd350f933")
    print("In main: ")
    print(final_tcd_data_dict)

if __name__=='__main__':
    main()





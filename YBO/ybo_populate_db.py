import requests
from requests_kerberos import HTTPKerberosAuth
import urllib3
import asyncio
import aiohttp
from requests.auth import HTTPBasicAuth
import argparse
import pandas as pd
import sqlite3
from sqlite3 import Error
import os
import math

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

"""
proxies_dict = \
    {
        "http": "http://child-prc.intel.com:913"
    }
"""
headers = {'Content-type': 'application/json'}

cid = 1
page_size = 50

start_at = 1
max_result = 10**5
base_url = 'https://hsdes-api.intel.com/rest/auth/query/execution/eql?max_results=' + str(max_result) + "&start_at=1"
username = "shaolida"
password = "M35DJ29kcX9UVke33nj7dX8giLX5dzvxFaeDUqXy7ixQmkgc="

def extract_relevant_tcs(release_affected):

    # Fetch all test cases for release_affected="release_affected" and planned_for="test_plan".
    tcs_content = []

    eql_test_cases = "\"eql\":\"select id, title, subject, parent_id, release_affected, test_case.test_cycle, central_firmware.test_case.planned_for where" \
                     " tenant='central_firmware' and subject='test_case' and release_affected = '{0}' " \
                     "\"".format(release_affected)
    payload_eql_tcs = """{""" + """{0}""".format(eql_test_cases) + """}"""

    response_eql_tcs = requests.post(base_url, verify = False, auth = HTTPBasicAuth("shaolida",
                    "M35DJ29kcX9UVke33nj7dX8giLX5dzvxFaeDUqXy7ixQmkgc="), headers = headers,
                                 data = payload_eql_tcs)
    #print(response_eql_tcs.status_code)
    if (response_eql_tcs.status_code == 200):                 
        resultant = response_eql_tcs.json()['data']
        print(resultant)
        return resultant

async def extract_relevant_trs(tc_id):
    temp_list = []
    global cid
    trs_content = []
    print("TC ID (1) = {0}".format(tc_id))
    print(cid)
    cid+=1
    
    
    eql_test_results = "\"eql\":\"select id, title, status_reason, test_result.test_cycle, test_result.actual_end," \
                       "submitted_date where " \
                       "tenant='central_firmware' and subject='test_case' " \
                       "and id = '{0}' and Parent(id='{0}'), LINK_parent-child(subject =" \
                       " 'test_result')\"".format(tc_id)

    payload_eql_trs = """{""" + """{0}""".format(eql_test_results) + """}"""

    async with aiohttp.ClientSession(trust_env = True ) as session:
        async with session.post(url = base_url, headers = headers,
                                data = payload_eql_trs, auth = aiohttp.BasicAuth("shaolida",
                    "M35DJ29kcX9UVke33nj7dX8giLX5dzvxFaeDUqXy7ixQmkgc=")) as resp:
            print("TC ID (2) = {0}".format(tc_id))
            content = await resp.json(content_type=None)
            # print("Temp List")
            temp_list.append(content)
            # print(temp_list)
            # print(resp.status)
            if 'data' in content:
                resultant = content['data']
                print("Response got.")
                return resultant[1:]
            else:
                print("TR response does not have data field.")
            print("TC ID (3) = {0}".format(tc_id))

            # if cid < 6:
            #     print("resultant in trs: {0}".format(resultant))
            # #trs_content.append(resultant[1:])
    
    #return resultant[1:]

async def get_tcs_with_trs(tc_id):
    
    tcs_with_trs = []
    tcs_without_trs = []
    return_tcd_id = ""
    bug_links_request_url = 'https://hsdes-api.intel.com/rest/auth/article/' + str(tc_id) + '/links'
    # Bug Links URL for KerberosAuth()
    # bug_links_request_url = 'https://hsdes-api.intel.com/rest/article/' + str(result["data"][0]["id"]) + '/links'
    # print("Requesting for TC links...")
    # bug_links_response = requests.get(bug_links_request_url, verify = False, auth = HTTPKerberosAuth(), headers = headers)
    async with aiohttp.ClientSession(trust_env = True ) as session:
        async with session.get(url = bug_links_request_url, auth = aiohttp.BasicAuth(username, password), headers = headers) as bug_links_resp:
        # print("Request to TC links complete.")
        # print("TC links response status code {0} found.".format(bug_links_response.status_code))
            bug_links_response = await bug_links_resp.json(content_type=None)
            print("Bug response = ", bug_links_response)
            if bug_links_resp.status == 200:
                # print("Bug links response: ")
                # print(bug_links_response.json())
                flag = False
                for x in bug_links_response["responses"]:
                    if x["subject"] == "test_result":
                        flag = True
                        tcs_with_trs.append(tc_id)
                        return str(tc_id)
                if not flag:
                    # logging.info("TC ID that does not have TR = {0}".format(tc_id))
                    print("TC ID that does not have TR = {0}".format(tc_id))
                    tcs_without_trs.append(tc_id)
                    return ""

async def extract_relevant_tcds(tc_id):

    tcds_content = []

    eql_test_case_defs = "\"eql\":\"select id, title, release_affected, central_firmware.test_case_definition.test_coverage_level, central_firmware.test_case_definition.processor, component, component_affected, domain, domain_affected where " \
                       "tenant='central_firmware' and subject='test_case_definition' " \
                       "and id = '{0}'\"".format(tc_id)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_defs) + """}"""

    async with aiohttp.ClientSession(trust_env = True ) as session:
        async with session.post(url = base_url, headers = headers,
                                data = payload_eql_tcds, auth = aiohttp.BasicAuth("shaolida",
                    "M35DJ29kcX9UVke33nj7dX8giLX5dzvxFaeDUqXy7ixQmkgc=")) as resp:
            content = await resp.json(content_type=None)
            if 'data' in content:
                resultant = content['data']
                return resultant

async def get_data(subject, n, id):
    if subject == "test_result":
        content = await extract_relevant_trs(id)
    elif subject == "test_case_definition":
        content = await extract_relevant_tcds(id)
    return content

async def get_all():

    list_of_programs = ["bios.alderlake"]
    table_name_list = ["ADL_N"]
    processor = "alderlake-n"
    tcs_content = []
    tcs_with_trs_content = []
    tc_ids = []
    tcd_ids = []
    tcs_with_trs_tcd_ids_all = []
    tasks = []
    for release_affected in list_of_programs:
        tcs_content = extract_relevant_tcs(release_affected)
        print("Type of tcs_content: {0}".format(type(tcs_content)))
        print("Length of tcs_content: {0}".format(len(tcs_content)))

        for j in range(len(tcs_content)):
            tc_ids.append(tcs_content[j]['id'])
            tcd_ids.append(tcs_content[j]['parent_id'])

        print("Length of tc_ids: {0}".format(len(tc_ids)))
        print("tc_ids = {0}".format(tc_ids[:10]))
        print("Length of tcd_ids: {0}".format(len(tcd_ids)))
        print("tcd_ids = {0}".format(tcd_ids[:10]))
        # for n, id in enumerate(tc_ids):
        test_results_all = []
        test_case_definitions_all = []

        idx_c = 0
        if len(tc_ids) > 200:
            print("Length of TC IDs is greater than 200. Length of TC IDs = {0}".format(len(tc_ids)))
            num = math.ceil(len(tc_ids) / 200)
            print("Num = ", num)
            for i in range(num):
                tcs_with_trs_tcd_ids = []
                tasks_tcs_with_trs = [get_tcs_with_trs(id) for id in tc_ids[idx_c: idx_c + 200]]
                # print(tasks_tcs_with_trs)
                tcs_with_trs = await asyncio.gather(*tasks_tcs_with_trs)
                print("TCs with TRs List = {0}".format(tcs_with_trs))
                if len(tcs_with_trs) > 0:
                    tcs_with_trs = [x for x in tcs_with_trs if x != ""]
                    for tr_count in range(len(tcs_with_trs)):
                        if tcs_with_trs[tr_count] in tc_ids:
                            tcs_with_trs_content.append(tcs_content[tc_ids.index(tcs_with_trs[tr_count])])
                            tcs_with_trs_tcd_ids.append(tcs_content[tc_ids.index(tcs_with_trs[tr_count])]['parent_id'])
                    tcs_with_trs_tcd_ids_all.extend(tcs_with_trs_tcd_ids)
                    tasks_trs = [get_data("test_result", n, id) for n, id in enumerate(tcs_with_trs)]
                    test_results = await asyncio.gather(*tasks_trs)
                    if len(test_results) > 0:
                        test_results_all.extend(test_results)
                        print("Test Results:")
                        print(test_results[0])
                        #print(test_results[1])
                        print("Length of Test Results: {0}".format(len(test_results)))
                        print("Length of Test Results All: {0}".format(len(test_results_all)))

                        task_tcds = [get_data("test_case_definition", n, id) for n, id in enumerate(tcs_with_trs_tcd_ids)]
                        test_case_definitions = await asyncio.gather(*task_tcds)
                        if len(test_case_definitions) > 0:
                            test_case_definitions_all.extend(test_case_definitions)
                            print("Test Case Definitions:")
                            print(test_case_definitions[0])
                            #print(test_case_definitions[1])
                            print("Length of Test Case Definitions: {0}".format(len(test_case_definitions)))
                            print("Length of Test Case Definitions All: {0}".format(len(test_case_definitions_all)))

                    else:
                        print("Test Results in else = {0}".format(test_results))
                else:
                    print("TCs with TRs List = {0}".format(tcs_with_trs))

                idx_c += 200

        elif len(tc_ids) <= 200 and len(tc_ids) > 0:
            print("Length of TC IDs is <= 200 and > 0 Length of TC IDs = {0}".format(len(tc_ids)))
            tasks_tcs_with_trs = [get_tcs_with_trs(id) for id in tc_ids]
            tcs_with_trs_tcd_ids = []
            # print(tasks_tcs_with_trs)
            tcs_with_trs = await asyncio.gather(*tasks_tcs_with_trs)
            print("TCs with TRs List = {0}".format(tcs_with_trs))
            if len(tcs_with_trs) > 0:
                tcs_with_trs = [x for x in tcs_with_trs if x != ""]
                for tr_count in range(len(tcs_with_trs)):
                    if tcs_with_trs[tr_count] in tc_ids:
                        tcs_with_trs_content.append(tcs_content[tc_ids.index(tcs_with_trs[tr_count])])
                        tcs_with_trs_tcd_ids.append(tcs_content[tc_ids.index(tcs_with_trs[tr_count])]['parent_id'])
                tasks_trs = [get_data("test_result", n, id) for n, id in enumerate(tcs_with_trs)]
                test_results = await asyncio.gather(*tasks_trs)
                if len(test_results) > 0:
                    test_results_all.extend(test_results)
                    print("Test Results:")
                    print(test_results[0])
                    print(test_results[1])
                    print("Length of Test Results: {0}".format(len(test_results)))
                    print("Length of Test Results All: {0}".format(len(test_results_all)))

                    task_tcds = [get_data("test_case_definition", n, id) for n, id in enumerate(tcs_with_trs_tcd_ids)]
                    test_case_definitions = await asyncio.gather(*task_tcds)
                    if len(test_case_definitions) > 0:
                        test_case_definitions_all.extend(test_case_definitions)
                        print("Test Case Definitions:")
                        print(test_case_definitions[0])
                        print(test_case_definitions[1])
                        print("Length of Test Case Definitions: {0}".format(len(test_case_definitions)))
                        print("Length of Test Case Definitions All: {0}".format(len(test_case_definitions_all)))

                else:
                    print("Test Results in else = {0}".format(test_results))
            else:
                print("TCs with TRs List = {0}".format(tcs_with_trs))
        
        else:
            print("Else Block - Length of TC IDs = {0}".format(len(tc_ids)))
        
        here = []
        count_all_results = 0

        for l in range(len(test_results_all)):
            count_all_results += len(test_results_all[l])

        all_data = [[] for l in range(count_all_results)]
        print("Count all results: {0}".format(count_all_results))
            
        j = 0
        for l in range(len(test_results_all)):
            for k in range(len(test_results_all[l])):
                all_data[j].append(test_case_definitions_all[l][0]['id'])
                all_data[j].append(test_case_definitions_all[l][0]['title'])
                all_data[j].append(test_case_definitions_all[l][0]['central_firmware.test_case_definition.test_coverage_level'])
                all_data[j].append(tcs_with_trs_content[l]['id'])
                all_data[j].append(tcs_with_trs_content[l]['title'])
                all_data[j].append(tcs_with_trs_content[l]['release_affected'])
                all_data[j].append(tcs_with_trs_content[l]['central_firmware.test_case.planned_for'])
                all_data[j].append(test_results_all[l][k]['id'])
                all_data[j].append(test_results_all[l][k]['title'])
                all_data[j].append(test_results_all[l][k]['status_reason'])
                all_data[j].append(test_results_all[l][k]['test_result.test_cycle'])
                all_data[j].append(test_results_all[l][k]['test_result.actual_end'])
                all_data[j].append(test_case_definitions_all[l][0]['domain'])
                all_data[j].append(test_case_definitions_all[l][0]['domain_affected'])
                all_data[j].append(test_case_definitions_all[l][0]['component'])
                all_data[j].append(test_case_definitions_all[l][0]['component_affected'])
                all_data[j].append(test_case_definitions_all[l][0]['central_firmware.test_case_definition.processor'])

                j = j + 1

        df = pd.DataFrame(all_data, columns = ["Test_Case_Definition_ID", "Test_Case_Definition_Title", "Test_Coverage_Level", "Test_Case_ID",
                                                "Test_Case_Title","Release_Affected", "Test_Plan", "Test_Result_ID",
                                                "Test_Result_Title", "Status_Reason", "Test_Cycle", "End_Date", "Domain", "Domain_Affected",
                                                "Component", "Component_Affected", "Processor"])

        new = df["Processor"].str.split(",", n = 20, expand = True)
        df = df.loc[(new[0] == processor) | (new[1] == processor) | (new[2] == processor) | (new[3] == processor) | (new[4] == processor) 
                    | (new[5] == processor) | (new[6] == processor) | (new[7] == processor) | (new[8] == processor) | (new[9] == processor) 
                    | (new[10] == processor) | (new[11] == processor) | (new[12] == processor) | (new[13] == processor) | (new[14] == processor) 
                    | (new[15] == processor) | (new[16] == processor) | (new[17] == processor) | (new[18] == processor) | (new[19] == processor)]
        df = df.drop('Processor', 1)

        conn = create_connection(os.path.join(os.getcwd( ), './DB/YBO_HSDES_TR_Database.db'))
        create_table_sql_query = "CREATE TABLE IF NOT EXISTS {0} (Test_Case_Definition_ID text NOT NULL, Test_Case_Definition_Title \
            text NOT NULL, Test_Coverage_Level text, Test_Case_ID text NOT NULL, Test_Case_Title text NOT NULL, Release_Affected text NOT NULL, Test_Plan text, \
            Test_Result_ID text NOT NULL, Test_Result_Title text NOT NULL, Status_Reason text, Test_Cycle text, End_Date text,Domain text, Domain_Affected text, \
            Component text, Component_Affected text);".format(table_name_list[list_of_programs.index(release_affected)])

        if conn is not None:
            create_table(conn, create_table_sql_query)

        df.to_sql(table_name_list[list_of_programs.index(release_affected)], conn, if_exists = 'append', index = False)

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all())
    print("All done!")
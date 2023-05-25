import sqlite3
from sqlite3 import Error
import argparse
import os
import logging
import json
import urllib3
import requests
from requests.auth import HTTPBasicAuth
import aiohttp
import asyncio
import math
import pandas as pd


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
base_url = 'https://hsdes-api.intel.com/rest/query/execution/eql?max_results=' + str(max_result) + "&start_at=1"
username = "hdave"
password = "LBOFGEoWwkuXOb5zlr0hZHW+ZwTE4EzIagalqLp8gdD22BbM#"

if not os.path.exists('Logs'):
    os.makedirs('Logs')

logging.basicConfig(filename='./Logs/ybo_deamon_logs.txt', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO)
logging.info("Imports done. Initializing variables...")

with open("/opt/ybobase/ybo_config.json") as json_data_file:
	json_data = json.load(json_data_file)
db_name = json_data["config"]["db_name"]
logging.info("Database name = {0}".format(db_name))

parser = argparse.ArgumentParser()
parser.add_argument('-p', help="Name of program")
# parser.add_argument('-l', help="Mandatory Test case level")
args = parser.parse_args()

program_name = args.p.lower()

table_names = {
    "bios.alderlake": "ADL",
    "bios.meteorlake": "MTL",
    "bios.rocketlake": "RKL",
    "bios.tigerlake": "TGL",
    "bios.arrowlake": "ARL",
    "bios.lunarlake": "LNL",
    "bios.raptorlake": "RPL",
    "bios.andersonlake": "ANL",
    "bios.fishhawkfalls": "FHF",
    "bios.eaglestream_sapphirerapids": "EGLSR",
}

table_name = table_names[args.p.lower()]
tr_to_tc_mapping = {}
tc_to_tcd_mapping = {}
test_results_data = []
test_cases_data = []
tcs_with_empty_response = []
tcds_with_empty_response = []
test_case_definitions_data = []
tc_ids = []
tcd_ids = []
all_data = []

db = sqlite3.connect("/opt/ybobase/DB/" + db_name)
print(db)
c = db.cursor()

query = "SELECT MAX(End_Date) FROM {0}".format(table_name)
print(query)
c.execute(query)
column_names = [description[0] for description in c.description]
print("Column Names {0}".format(column_names))
max_end_date = c.fetchall()[0][0]
print(max_end_date)

# max_end_date = "2021ww40.5" # for testing

# database format -> 
# TCD_ID (0), TCD_TITLE (1), TEST_COVERAGE_LEVEL (2), TEST_CASE_ID (3), TEST_CASE_TITLE (4), RELEASE_AFFECTED (5), TEST_PLAN (6), 
# TEST_RESULT_ID (7), TEST_RESULT_TITLE (8), STATUS_REASON (9), TEST_CYCLE (10), END_DATE (11), DOMAIN (12), DOMAIN_AFFECTED (13), 
# COMPONENT (14), COMPONENT_AFFECTED (15)

async def extract_tcs_data(tc_id):
    
    global tcs_with_empty_response, tr_to_tc_mapping

    # print("------------- Inside Extract TCs Data function ----------------------")

    eql_test_cases = "\"eql\":\"select id, title, subject, parent_id, release_affected, test_case.test_cycle, central_firmware.test_case.planned_for where " \
                       "tenant='central_firmware' and subject='test_case' " \
                       "and id = '{0}'\"".format(tc_id)

    payload_eql_tcs = """{""" + """{0}""".format(eql_test_cases) + """}"""

    async with aiohttp.ClientSession(trust_env = True ) as session:
        async with session.post(url = base_url, headers = headers,
                                data = payload_eql_tcs, auth = aiohttp.BasicAuth("hdave",
                    "LBOFGEoWwkuXOb5zlr0hZHW+ZwTE4EzIagalqLp8gdD22BbM=")) as resp:
            if resp.status == 200:
                content = await resp.json(content_type=None)

                if 'data' in content:
                    resultant = content['data']
                    # print("********************************************************************************************************************************")
                    # print("TC Response got for TC ID: {0}.".format(tc_id))
                else:
                    print("TC response does not have data field.")

                # print("TC Content for TC ID: {0}".format(tc_id))
                # print(resultant)

                if resultant == []:
                    tcs_with_empty_response.append(tc_id)
                    tr_to_tc_mapping = {k:v for k, v in tr_to_tc_mapping.items() if v != tc_id}

                # print("********************************************************************************************************************************")

                return resultant

            else:
                print("TC Response code = ", resp.status)
                print("TC Response ---------------------------------------------------------------------------------------------------------")
                print(resp.json())
                tcs_with_empty_response.append(tc_id)
                tr_to_tc_mapping = {k:v for k, v in tr_to_tc_mapping.items() if v != tc_id}


                return []

async def extract_tcds_data(tcd_id):

    global tcds_with_empty_response, tc_to_tcd_mapping
    
    # print("------------- Inside Extract TCDs Data function ----------------------")
    
    eql_test_case_definitions = "\"eql\":\"select id, title, release_affected, central_firmware.test_case_definition.test_coverage_level, component, component_affected, domain, domain_affected where " \
                       "tenant='central_firmware' and subject='test_case_definition' " \
                       "and id = '{0}'\"".format(tcd_id)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""

    async with aiohttp.ClientSession(trust_env = True ) as session:
        async with session.post(url = base_url, headers = headers,
                                data = payload_eql_tcds, auth = aiohttp.BasicAuth("hdave",
                    "LBOFGEoWwkuXOb5zlr0hZHW+ZwTE4EzIagalqLp8gdD22BbM=")) as resp:
            if resp.status == 200:
                content = await resp.json(content_type=None)

                if 'data' in content:
                    resultant = content['data']
                    # print("TCD Response got.")
                else:
                    print("TCD response does not have data field.")

                # print("TCD Content -----------------------------------------------------------------------------------------------------")
                # print(resultant)

                if resultant == []:
                    tcds_with_empty_response.append(tcd_id)
                    tc_to_tcd_mapping = {k:v for k, v in tc_to_tcd_mapping.items() if v != tcd_id}


                return resultant

            else:
                print("TCD Response code = ", resp.status)
                print("TCD Response ---------------------------------------------------------------------------------------------------------")
                print(resp.json())
                tcds_with_empty_response.append(tcd_id)
                tc_to_tcd_mapping = {k:v for k, v in tc_to_tcd_mapping.items() if v != tcd_id}

                return []

def get_tr_data():

    global test_results_data, tc_ids, tr_to_tc_mapping, max_end_date, program_name, table_name, table_names

    eql_test_results_query = "\"eql\":\"select id, title, status_reason, test_result.test_cycle, test_result.actual_end, parent_id where" \
                        " tenant='central_firmware' and subject='test_result' and release = '{0}' and test_result.actual_end > '{1}'" \
                        "\"".format(program_name, max_end_date)
    payload_eql_test_result_query = """{""" + """{0}""".format(eql_test_results_query) + """}"""

    print(eql_test_results_query)

    response_eql_test_results = requests.post(base_url, verify = False, auth = HTTPBasicAuth("hdave",
                    "LBOFGEoWwkuXOb5zlr0hZHW+ZwTE4EzIagalqLp8gdD22BbM="), headers = headers,
                                    data = payload_eql_test_result_query)

    if response_eql_test_results.status_code == 200:

        test_results_data = response_eql_test_results.json()['data']

        print("Test Results Data ----------------------------------------------------------------------------------------------")
        print(len(test_results_data))
        print(test_results_data[:2])

        for single_tr_data in test_results_data:
            tc_ids.append(single_tr_data['parent_id'])
            tr_to_tc_mapping[single_tr_data['id']] = single_tr_data['parent_id']

        print("TC_IDs ----------------------------------------------------------------------------------------------------------")
        # print(tc_ids)
        print(len(tc_ids))

    else:
        print("Response code = ", response_eql_test_results.status_code)
        print("Response ---------------------------------------------------------------------------------------------------------")
        print(response_eql_test_results.json())

async def get_data(subject, n, id):
    if subject == "test_case":
        content = await extract_tcs_data(id)
    elif subject == "test_case_definition":
        content = await extract_tcds_data(id)
    return content

def get_tc_data(tc_id):

    global test_results_data, tc_ids, tr_to_tc_mapping, max_end_date, program_name, table_name, table_names

    print("------------- Inside Extract TCs Data function Regular ----------------------")

    eql_test_cases = "\"eql\":\"select id, title, subject, parent_id, release_affected, test_case.test_cycle, central_firmware.test_case.planned_for where " \
                       "tenant='central_firmware' and subject='test_case' " \
                       "and id = '{0}'\"".format(tc_id)

    payload_eql_tcs = """{""" + """{0}""".format(eql_test_cases) + """}"""

    print(eql_test_cases)

    response_eql_test_cases = requests.post(base_url, verify = False, auth = HTTPBasicAuth("hdave",
                    "LBOFGEoWwkuXOb5zlr0hZHW+ZwTE4EzIagalqLp8gdD22BbM="), headers = headers,
                                    data = payload_eql_tcs)

    if response_eql_test_cases.status_code == 200:

        test_case_data = response_eql_test_cases.json()['data']

        print("Test Case Data Regular for TC ID: {0} ----------------------------------------------------------------------------------------------".format(tc_id))
        print(len(test_case_data))
        print(test_case_data)

    else:
        print("Response code = ", response_eql_test_cases.status_code)
        print("Response ---------------------------------------------------------------------------------------------------------")
        print(response_eql_test_cases.json())


async def run_daemon():

    global tc_ids, tr_to_tc_mapping, test_results_data, test_cases_data, tcd_ids, tc_to_tcd_mapping, test_case_definitions_data

    test_cases_data_all = []
    test_case_definitions_data_all = []

    get_tr_data()

    tc_ids = list(set(tc_ids))

    # get_tc_data("16014703270")
    idx_c = 0
    if len(tc_ids) > 500:
        print("Length of TC IDs is greater than 500. Length of TC IDs = {0}".format(len(tc_ids)))
        num = math.ceil(len(tc_ids) / 500)
        
        print("Num = ", num)
        for e in range(num):
            last_idx = idx_c + 500
            if last_idx > len(tc_ids):
                last_idx = len(tc_ids) + 1
            task_tcs = [get_data("test_case", n, id) for n, id in enumerate(tc_ids[idx_c: last_idx])]
            test_cases_data = await asyncio.gather(*task_tcs)

            test_cases_data = [data_row for data_row in test_cases_data if len(data_row) >= 1 and data_row != []]

            if len(test_cases_data) > 0:
                test_cases_data_all.extend(test_cases_data)

                # print("TR to TC Mapping Length (After): {0}".format(len(tr_to_tc_mapping)))
                # print("TR to TC Mapping (After): {0}".format(tr_to_tc_mapping))

                # print("Test Cases Data --------------------------------------------------------------------------------------------------------")
                # print(len(test_cases_data))
                # for i in test_cases_data:
                #     print("**********************************************************************************************************************")
                #     print(i)

                for single_tc_data in test_cases_data:
                    if len(single_tc_data) >= 1:
                        if single_tc_data[0]['parent_id'] not in tcd_ids:
                            tcd_ids.append(single_tc_data[0]['parent_id'])
                        tc_to_tcd_mapping[single_tc_data[0]['id']] = single_tc_data[0]['parent_id']

                print("TCD IDs and TC to TCD Mapping -----------------------------------------------------------------------------------------------------------------")
                # print(tcd_ids)
                print(len(tcd_ids))
                print(len(tc_to_tcd_mapping))

                print("Length of TC Data = {0}".format(len(test_cases_data)))
                print("Length of TC Data All = {0}".format(len(test_cases_data_all)))

            idx_c += 500

    elif len(tc_ids) <= 500 and len(tc_ids) > 0:

        print("Length of TC IDs is less than 500.")
        task_tcs = [get_data("test_case", n, id) for n, id in enumerate(tc_ids)]
        test_cases_data = await asyncio.gather(*task_tcs)

        test_cases_data = [data_row for data_row in test_cases_data if len(data_row) >= 1 and data_row != []]

        if len(test_cases_data) > 0:
            test_cases_data_all.extend(test_cases_data)

            # print("TR to TC Mapping Length (After): {0}".format(len(tr_to_tc_mapping)))
            # print("TR to TC Mapping (After): {0}".format(tr_to_tc_mapping))

            # print("Test Cases Data --------------------------------------------------------------------------------------------------------")
            # print(len(test_cases_data))
            # for i in test_cases_data:
            #     print("**********************************************************************************************************************")
            #     print(i)

            for single_tc_data in test_cases_data:
                if len(single_tc_data) >= 1:
                    tcd_ids.append(single_tc_data[0]['parent_id'])
                    tc_to_tcd_mapping[single_tc_data[0]['id']] = single_tc_data[0]['parent_id']

            print("TCD IDs -----------------------------------------------------------------------------------------------------------------")
            # print(tcd_ids)
            print(len(tcd_ids))

            print("Length of TC Data = {0}".format(len(test_cases_data)))
            print("Length of TC Data All = {0}".format(len(test_cases_data_all)))
            
    else:
        print("Else Block - Length of TC IDs = {0}".format(len(tc_ids)))


    print("Comparison of TC data length and TR to TC mapping.")
    print("TC Data length = {0}".format(len(test_cases_data_all)))
    print("TR to TC mapping length = {0}".format(len(tr_to_tc_mapping)))
    print("TCD IDs length = {0}".format(len(tcd_ids)))
    print("TC to TCD mapping length = {0}".format(len(tc_to_tcd_mapping)))

    idx_d = 0
    if len(tcd_ids) > 500:
        print("Length of TCD IDs is greater than 500. Length of TCD IDs = {0}".format(len(tcd_ids)))
        num1 = math.ceil(len(tcd_ids) / 500)
        
        print("Num1 = ", num1)
        for f in range(num1):
            last_idx_d = idx_d + 500
            if last_idx_d > len(tcd_ids):
                last_idx_d = len(tcd_ids) + 1
            
            task_tcds = [get_data("test_case_definition", n, id) for n, id in enumerate(tcd_ids[idx_d: last_idx_d])]
            test_case_definitions_data = await asyncio.gather(*task_tcds)
            
            test_case_definitions_data = [data_row for data_row in test_case_definitions_data if len(data_row) >= 1 and data_row != []]

            if len(test_case_definitions_data) > 0:
                test_case_definitions_data_all.extend(test_case_definitions_data)

                # print("Test Case Definitions Data --------------------------------------------------------------------------------------------------------")
                # print(len(test_case_definitions_data))
                # print(test_case_definitions_data[:2])

                print("Length of TCD Data = {0}".format(len(test_case_definitions_data)))
                print("Length of TCD Data All = {0}".format(len(test_case_definitions_data_all)))

            idx_d += 500

    elif len(tcd_ids) <= 500 and len(tcd_ids) > 0:

        print("Length of TCD IDs is less than 500.")
        
        task_tcds = [get_data("test_case_definition", n, id) for n, id in enumerate(tcd_ids)]
        test_case_definitions_data = await asyncio.gather(*task_tcds)

        test_case_definitions_data = [data_row for data_row in test_case_definitions_data if len(data_row) >= 1 and data_row != []]
        
        if len(test_case_definitions_data) > 0:
            test_case_definitions_data_all.extend(test_case_definitions_data)

            # print("Test Case Definitions Data --------------------------------------------------------------------------------------------------------")
            # print(len(test_case_definitions_data))
            # print(test_case_definitions_data[:2])

            print("Length of TCD Data = {0}".format(len(test_case_definitions_data)))
            print("Length of TCD Data All = {0}".format(len(test_case_definitions_data_all)))
            
    else:
        print("Else Block - Length of TCD IDs = {0}".format(len(tc_ids)))

    
    print("Comparison of TCD data length and TC to TCD mapping.")
    print("TC Data length = {0}".format(len(test_cases_data_all)))
    print("TR to TC mapping length = {0}".format(len(tr_to_tc_mapping)))
    print("TCD Data length = {0}".format(len(test_case_definitions_data_all)))
    print("TC to TCD mapping length = {0}".format(len(tc_to_tcd_mapping)))
    print("TCD IDs length = {0}".format(len(tcd_ids)))

    temp_tr_data = []
    for elem in test_results_data:
        if elem['id'] in tr_to_tc_mapping.keys():
            temp_tr_data.append(elem)

    test_results_data = temp_tr_data

    # database format -> 
    # TCD_ID (0), TCD_TITLE (1), TEST_COVERAGE_LEVEL (2), TEST_CASE_ID (3), TEST_CASE_TITLE (4), RELEASE_AFFECTED (5), TEST_PLAN (6), 
    # TEST_RESULT_ID (7), TEST_RESULT_TITLE (8), STATUS_REASON (9), TEST_CYCLE (10), END_DATE (11), DOMAIN (12), DOMAIN_AFFECTED (13), 
    # COMPONENT (14), COMPONENT_AFFECTED (15)
    print("Length of test results data = ", len(test_results_data))

    print("Checking format Test Results: -------------------------------------------------------")
    print(test_results_data[:2])
    print("Checking format Test Cases: -------------------------------------------------------")
    print(test_cases_data_all[:2])
    print("Checking format Test Case Definitions: -------------------------------------------------------")
    print(test_case_definitions_data_all[:2])
    print("Empty TCs = ", len(tcs_with_empty_response))
    print("Empty TCDs = ", len(tcds_with_empty_response))
    data_prep_for_db = []
    for idx in range(len(test_results_data)):
        # print(idx)
        # print("Inside")
        # print(test_results_data[idx])
        # print(test_results_data[idx]['id'])
        # print(tr_to_tc_mapping[test_results_data[idx]['id']])
        # for tc_row in test_cases_data_all:
        #     print(tc_row)
        #     if tc_row[0]['id'] == tr_to_tc_mapping[test_results_data[idx]['id']]:
        #         temp_tc = tc_row[0]
        # print("Temp TC = ", temp_tc)
        
        temp_tc = [tc_row[0] for tc_row in test_cases_data_all if tc_row[0]['id'] == tr_to_tc_mapping[test_results_data[idx]['id']]]
        if tr_to_tc_mapping[test_results_data[idx]['id']] in tc_to_tcd_mapping.keys():
            temp_tcd = [tcd_row[0] for tcd_row in test_case_definitions_data_all if tcd_row[0]['id'] == tc_to_tcd_mapping[tr_to_tc_mapping[test_results_data[idx]['id']]]]
            print(temp_tcd)
            data_prep_for_db.append([
                temp_tcd[0]['id'], 
                temp_tcd[0]['title'],
                temp_tcd[0]['central_firmware.test_case_definition.test_coverage_level'],
                temp_tc[0]['id'],
                temp_tc[0]['title'],
                temp_tc[0]['release_affected'],
                temp_tc[0]['central_firmware.test_case.planned_for'],
                test_results_data[idx]['id'],
                test_results_data[idx]['title'],
                test_results_data[idx]['status_reason'],
                test_results_data[idx]['test_result.test_cycle'],
                test_results_data[idx]['test_result.actual_end'],
                temp_tcd[0]['domain'],
                temp_tcd[0]['domain_affected'],
                temp_tcd[0]['component'],
                temp_tcd[0]['component_affected']
            ])

    df = pd.DataFrame(data_prep_for_db, columns = ["Test_Case_Definition_ID", "Test_Case_Definition_Title", "Test_Coverage_Level", "Test_Case_ID",
                                            "Test_Case_Title","Release_Affected", "Test_Plan", "Test_Result_ID",
                                            "Test_Result_Title", "Status_Reason", "Test_Cycle", "End_Date", "Domain", "Domain_Affected",
                                            "Component", "Component_Affected"])


        # conn = create_connection(os.path.join(os.getcwd( ), './DB/', db_name))
    if len(test_results_data) >= 1:
        create_table_sql_query = "CREATE TABLE IF NOT EXISTS {0} (Test_Case_Definition_ID text NOT NULL, Test_Case_Definition_Title \
            text NOT NULL, Test_Coverage_Level text, Test_Case_ID text NOT NULL, Test_Case_Title text NOT NULL, Release_Affected text NOT NULL, Test_Plan text, \
            Test_Result_ID text NOT NULL, Test_Result_Title text NOT NULL, Status_Reason text, Test_Cycle text, End_Date text, Domain text, Domain_Affected text, \
            Component text, Component_Affected text);".format(table_name)

        c.execute(create_table_sql_query)

        df.to_sql(table_name, db, if_exists = 'append', index = False)

        write_release_affected_query = "UPDATE {0} SET Release_Affected = '{1}'".format(table_name, program_name)
        c.execute(write_release_affected_query)

    else:
        print("No new data available !!!")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_daemon())
    print("All done!")

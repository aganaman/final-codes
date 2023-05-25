import sqlite3
from sqlite3 import Error
import argparse
import os
import logging
import json
import urllib3
import requests
from requests.auth import HTTPBasicAuth
from requests_kerberos import HTTPKerberosAuth
import aiohttp
import asyncio
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
username = "shaolida"
password = "M65LqnLkcunT3/zl4JRaZEqdOVbbj+wV3illQqTCm34F7fiA="

if not os.path.exists('Logs'):
    os.makedirs('Logs')

logging.basicConfig(filename='./Logs/ybo_deamon_logs.txt', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO)
logging.info("Imports done. Initializing variables...")

with open("ybo_config.json") as json_data_file:
	json_data = json.load(json_data_file)
db_name = json_data["config"]["db_name"]
logging.info("Database name = {0}".format(db_name))

parser = argparse.ArgumentParser()
parser.add_argument('-p', help="Name of program")
parser.add_argument('-s', help="Name of SKU", required=False)
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
    "ifwi.eaglestream_sapphirerapids": "EGLSR_IFWI" 
}

name = table_names[args.p.lower()]
if name in ["ANL", "FHF", "EGLSR", "EGLSR_IFWI"]:
    table_name = name
else:
    table_name = name +'_'+ args.s.upper()

tr_to_tc_mapping = {}
tc_to_tcd_mapping = {}
test_results_data = []
test_cases_data = []
tcs_with_empty_response = []
test_case_definitions_data = []
tc_ids = []
tcd_ids = []
all_data = []

db = sqlite3.connect("./DB/" + db_name)
print(db)
c = db.cursor() 

query = "SELECT MAX(End_Date) FROM {0}".format(table_name)
print(query)
c.execute(query)
column_names = [description[0] for description in c.description]
print("Column Names {0}".format(column_names))
max_end_date = c.fetchall()[0][0]
print(max_end_date)

#max_end_date = "2021ww28.1" # for testing

# database format -> 
# TCD_ID (0), TCD_TITLE (1), TEST_COVERAGE_LEVEL (2), TEST_CASE_ID (3), TEST_CASE_TITLE (4), RELEASE_AFFECTED (5), TEST_PLAN (6), 
# TEST_RESULT_ID (7), TEST_RESULT_TITLE (8), STATUS_REASON (9), TEST_CYCLE (10), END_DATE (11), DOMAIN (12), DOMAIN_AFFECTED (13), 
# COMPONENT (14), COMPONENT_AFFECTED (15)

async def extract_tcs_data(tc_id):
    
    global tcs_with_empty_response, tr_to_tc_mapping

    print("------------- Inside Extract TCs Data function ----------------------")

    eql_test_cases = "\"eql\":\"select id, title, subject, parent_id, release_affected, test_case.test_cycle, central_firmware.test_case.planned_for where " \
                       "tenant='central_firmware' and subject='test_case' " \
                       "and id = '{0}'\"".format(tc_id)

    payload_eql_tcs = """{""" + """{0}""".format(eql_test_cases) + """}"""

    async with aiohttp.ClientSession(trust_env = True ) as session:
        async with session.post(url = base_url, headers = headers,
                                data = payload_eql_tcs, auth = aiohttp.KerberosAuth()) as resp:
            if resp.status == 200:
                content = await resp.json(content_type=None)

                if 'data' in content:
                    resultant = content['data']
                    print("********************************************************************************************************************************")
                    print("TC Response got for TC ID: {0}.".format(tc_id))
                else:
                    print("TC response does not have data field.")

                print("TC Content for TC ID: {0}".format(tc_id))
                print(resultant)

                if resultant == []:
                    tcs_with_empty_response.append(tc_id)
                    tr_to_tc_mapping = {k:v for k, v in tr_to_tc_mapping.items() if v != tc_id}

                print("********************************************************************************************************************************")

                return resultant

            else:
                print("TC Response code = ", resp.status)
                print("TC Response ---------------------------------------------------------------------------------------------------------")
                print(resp.json())

                return []

async def extract_tcds_data(tcd_id):

    print("------------- Inside Extract TCDs Data function ----------------------")
    
    eql_test_case_definitions = "\"eql\":\"select id, title, release_affected, central_firmware.test_case_definition.test_coverage_level, central_firmware.test_case_definition.processor, component, component_affected, domain, domain_affected where " \
                       "tenant='central_firmware' and subject='test_case_definition' " \
                       "and id = '{0}'\"".format(tcd_id)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""

    async with aiohttp.ClientSession(trust_env = True ) as session:
        async with session.post(url = base_url, headers = headers,
                                data = payload_eql_tcds, auth = aiohttp.KerberosAuth()) as resp:
            if resp.status == 200:
                content = await resp.json(content_type=None)

                if 'data' in content:
                    resultant = content['data']
                    print("TCD Response got.")
                else:
                    print("TCD response does not have data field.")

                # print("TCD Content -----------------------------------------------------------------------------------------------------")
                # print(resultant)

                return resultant

            else:
                print("TCD Response code = ", resp.status)
                print("TCD Response ---------------------------------------------------------------------------------------------------------")
                print(resp.json())

                return []

def get_tr_data():

    global test_results_data, tc_ids, tr_to_tc_mapping, max_end_date, program_name, table_name, table_names

    eql_test_results_query = "\"eql\":\"select id, title, status_reason, test_result.test_cycle, test_result.actual_end, parent_id where" \
                        " tenant='central_firmware' and subject='test_result' and release = '{0}' and test_result.actual_end > '{1}'" \
                        "\"".format(program_name, max_end_date)
    payload_eql_test_result_query = """{""" + """{0}""".format(eql_test_results_query) + """}"""

    print(eql_test_results_query)
    logging.info("eql-test-results-query:--------------------------------------------",eql_test_results_query)
    logging.info("payload-eql-test result query:----------------------------",eql_test_results_query)
    #base_url = 'https://hsdes-api.intel.com/rest/query/execution/eql?max_results=' + str(max_result) + "&start_at=1"


    response_eql_test_results = requests.post(base_url, verify = False, auth = HTTPKerberosAuth(), headers = headers,
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
        print(tc_ids)
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

    response_eql_test_cases = requests.post(base_url, verify = False, auth = HTTPKerberosAuth(), headers = headers,
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

    get_tr_data()

    print("TR to TC Mapping Length (Before): {0}".format(len(tr_to_tc_mapping)))
    print("TR to TC Mapping (Before): {0}".format(tr_to_tc_mapping))

    idx_c = 0
    if len(test_results_data) > 200:
        # get_tc_data("16014703270")

        task_tcs = [get_data("test_case", n, id) for n, id in enumerate(tc_ids[idx_c: idx_c + 200])]
        test_cases_data = await asyncio.gather(*task_tcs)

        print("TR to TC Mapping Length (After): {0}".format(len(tr_to_tc_mapping)))
        print("TR to TC Mapping (After): {0}".format(tr_to_tc_mapping))

        print("Test Cases Data --------------------------------------------------------------------------------------------------------")
        print(len(test_cases_data))
        # for i in test_cases_data:
        #     print("**********************************************************************************************************************")
        #     print(i)

        for single_tc_data in test_cases_data:
            if len(single_tc_data) >= 1:
                tcd_ids.append(single_tc_data[0]['parent_id'])
                tc_to_tcd_mapping[single_tc_data[0]['id']] = single_tc_data[0]['parent_id']

        print("TCD IDs -----------------------------------------------------------------------------------------------------------------")
        print(tcd_ids)
        print(len(tcd_ids))

        task_tcds = [get_data("test_case_definition", n, id) for n, id in enumerate(tcd_ids[idx_c: idx_c + 200])]
        test_case_definitions_data = await asyncio.gather(*task_tcds)

        print("Test Case Definitions Data --------------------------------------------------------------------------------------------------------")
        print(len(test_case_definitions_data))
        print(test_case_definitions_data[:2])

        temp_tr_data = []
        for elem in test_results_data:
            if elem['id'] in tr_to_tc_mapping.keys():
                temp_tr_data.append(elem)

        test_results_data = temp_tr_data
        idx_c += 200

    elif len(test_results_data) <= 200 and len(test_results_data) > 0:
        # get_tc_data("16014703270")

        task_tcs = [get_data("test_case", n, id) for n, id in enumerate(tc_ids)]
        test_cases_data = await asyncio.gather(*task_tcs)

        print("TR to TC Mapping Length (After): {0}".format(len(tr_to_tc_mapping)))
        print("TR to TC Mapping (After): {0}".format(tr_to_tc_mapping))

        print("Test Cases Data --------------------------------------------------------------------------------------------------------")
        print(len(test_cases_data))
        # for i in test_cases_data:
        #     print("**********************************************************************************************************************")
        #     print(i)

        for single_tc_data in test_cases_data:
            if len(single_tc_data) >= 1:
                tcd_ids.append(single_tc_data[0]['parent_id'])
                tc_to_tcd_mapping[single_tc_data[0]['id']] = single_tc_data[0]['parent_id']

        print("TCD IDs -----------------------------------------------------------------------------------------------------------------")
        print(tcd_ids)
        print(len(tcd_ids))

        task_tcds = [get_data("test_case_definition", n, id) for n, id in enumerate(tcd_ids)]
        test_case_definitions_data = await asyncio.gather(*task_tcds)

        print("Test Case Definitions Data --------------------------------------------------------------------------------------------------------")
        print(len(test_case_definitions_data))
        print(test_case_definitions_data[:2])

        temp_tr_data = []
        for elem in test_results_data:
            if elem['id'] in tr_to_tc_mapping.keys():
                temp_tr_data.append(elem)

        test_results_data = temp_tr_data
    
    # database format -> 
    # TCD_ID (0), TCD_TITLE (1), TEST_COVERAGE_LEVEL (2), TEST_CASE_ID (3), TEST_CASE_TITLE (4), RELEASE_AFFECTED (5), TEST_PLAN (6), 
    # TEST_RESULT_ID (7), TEST_RESULT_TITLE (8), STATUS_REASON (9), TEST_CYCLE (10), END_DATE (11), DOMAIN (12), DOMAIN_AFFECTED (13), 
    # COMPONENT (14), COMPONENT_AFFECTED (15)

    data_prep_for_db = []
    for idx in range(len(test_results_data)):
        #print(idx)
        try:
            temp_tc = [tc_row[0] for tc_row in test_cases_data if tc_row[0]['id'] == tr_to_tc_mapping[test_results_data[idx]['id']]]
            temp_tcd = [tcd_row[0] for tcd_row in test_case_definitions_data if tcd_row[0]['id'] == tc_to_tcd_mapping[tr_to_tc_mapping[test_results_data[idx]['id']]]]
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
                temp_tcd[0]['component_affected'],
                temp_tcd[0]['central_firmware.test_case_definition.processor']
            ])        
        except KeyError:
            print("KeyError")

    df = pd.DataFrame(data_prep_for_db, columns = ["Test_Case_Definition_ID", "Test_Case_Definition_Title", "Test_Coverage_Level", "Test_Case_ID",
                                            "Test_Case_Title","Release_Affected", "Test_Plan", "Test_Result_ID",
                                            "Test_Result_Title", "Status_Reason", "Test_Cycle", "End_Date", "Domain", "Domain_Affected",
                                            "Component", "Component_Affected", "Processor"])
    
    program = program_name.split(".")
    processor = program[1]+'-'+args.s.lower()
    new = df["Processor"].str.split(",", n = 20, expand = True)
    df = df.loc[(new[0] == processor) | (new[1] == processor) | (new[2] == processor) | (new[3] == processor) | (new[4] == processor) 
                | (new[5] == processor) | (new[6] == processor) | (new[7] == processor) | (new[8] == processor) | (new[9] == processor) 
                | (new[10] == processor) | (new[11] == processor) | (new[12] == processor) | (new[13] == processor) | (new[14] == processor) 
                | (new[15] == processor) | (new[16] == processor) | (new[17] == processor) | (new[18] == processor)]
    df = df.drop('Processor', 1)

    # conn = create_connection(os.path.join(os.getcwd( ), './DB/', db_name))
    create_table_sql_query = "CREATE TABLE IF NOT EXISTS {0} (Test_Case_Definition_ID text NOT NULL, Test_Case_Definition_Title \
        text NOT NULL, Test_Coverage_Level text, Test_Case_ID text NOT NULL, Test_Case_Title text NOT NULL, Release_Affected text NOT NULL, Test_Plan text, \
        Test_Result_ID text NOT NULL, Test_Result_Title text NOT NULL, Status_Reason text, Test_Cycle text, End_Date text, Domain text, Domain_Affected text, \
        Component text, Component_Affected text);".format(table_name)

    c.execute(create_table_sql_query)

    df.to_sql(table_name, db, if_exists = 'append', index = False)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_daemon())
    print("Collecting data from HSD-ES completed!")

    df = pd.read_sql_query("SELECT * FROM {0}".format(table_name), db)
    print(df)
    df = df.sort_values(by = "End_Date", ascending=False)
    end_date = df.iloc[0:1,11:12]
    date = str(end_date)
    x = date.split(".")
    work_day = x[1]
    y = x[0].split("ww")
    y1 = y[0].split(" ")
    y2 = y1[11]
    ww = int(y[1])
    new_ww = ww - 24
    if (new_ww > 0):
        work_week = new_ww
        year = y2
    elif(new_ww < 0):
        work_week = 52 + new_ww
        year = int(y2) -1

    date = str(year) +'ww'+ str(work_week) +'.'+ str(work_day)
    print(date)
    df.drop(df[(df['End_Date'] <= date)].index, inplace=True)
    print(df)
    df.to_sql(table_name, db, if_exists = 'replace', index = False)
    print("Successfully deleted the old data from database!")
    print("All done!")

#    py ybo_daemon.py -p bios.raptorlake -s S
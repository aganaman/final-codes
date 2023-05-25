import re
import os
import pandas as pd
import numpy as np
import sqlite3
import json
import requests
import urllib3
from requests.auth import HTTPBasicAuth
from requests_kerberos import HTTPKerberosAuth
import argparse

# py merge_report.py -p bios.raptorlake -c C:\Users\shaolida\Downloads\Practice\1\Merge_config.JSON -m C:\Users\shaolida\Downloads\Practice\1\merge_report
# py ybo_merge_report.py -p bios.raptorlake -s P -c C:\NAMAN\Share\YBO\ybo_config.JSON

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


"""
Manual Report Format:
1) Name of the file should have BIOS version
2) Name of the file should have test plan name (BAT/FV/Orange/Blue)
3) All the test results should be in first sheet of excel
4) First column should be named as TCD_ID (HSDES Test Case Definition ID)
5) Second column should be named as TCD_Title (HSDES Test Case Definition Title)
5) One of column should be Status (Having values -> "Pass" / "Fail" / "Blocked")
6) Excel file (reports) should not be open while running this script

"""

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
username = "hdave"
password = "LBOFGEoWwkuXOb5zlr0hZHW+ZwTE4EzIagalqLp8gdD22BbM="


parser = argparse.ArgumentParser()
parser.add_argument('-p', help="Name of program (bios.alderlake, bios.raptorlake) ")
parser.add_argument('-s', help="Name of SKU (S, M, P)",required=False)
parser.add_argument('-ch', help="Name of Charter (BIOS, IFWI, SECURITY)")
parser.add_argument('-c', help="Config file path", required=False)
args = parser.parse_args()

with open("ybo_config.json") as json_data_file:
	json_data = json.load(json_data_file)
db_name = json_data["config"]["db_name"]
db = sqlite3.connect("./DB/" + db_name)
c = db.cursor()

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
    "ifwi.eaglestream_sapphirerapids": "EGLSR_IFWI",
    "ifwi.alderlake": "ADL",
    "ifwi.meteorlake": "MTL",
    "ifwi.rocketlake": "RKL",
    "ifwi.tigerlake": "TGL",
    "ifwi.arrowlake": "ARL",
    "ifwi.lunarlake": "LNL",
    "ifwi.raptorlake": "RPL",
    "bios.kaseyville": "GNR_D",
    "bios.birchstream": "GNR_AP"

}

name = table_names[args.p.lower()]
if name in ["ANL", "FHF", "EGLSR", "EGLSR_IFWI", "GNR_D", "GNR_AP"]:
    table_name = name
else:
    #table_name = name + '_' + args.s.upper() + '_BIOS_Test'
    table_name = name + '_' + args.s.upper()
print(table_name)
table = {
    "RPL_S" : "2020",
    "RPL_S_Test" : "2020",
    "RPL_S_BIOS_Test" : "2020",
    "RPL_P_Test" : "2020",
    "RPL_P":"2020",
    "RPL_SBGA":"2020",
    "MTL_S":"2021",
    "MTL_P":"2021",
    "ARL_S":"2021",
    "MTL_M":"2021",
    "LNL_M":"2022",
    "ADL_N":"2020",
    "ADL_S":"2020",
    "ADL_M":"2020",
    "ADL_P":"2020",
    "ADL_SBGA":"2020",
    "GNR_D": "2021",
    "GNR_AP": "2021"
}
first_year_value = table[table_name]

# Path to the reports
path = r'C:\NAMAN\Share\YBO\MTL\MTL-S\MTL-S BIOS  Manual Reports\BAT'
merge_folder = os.listdir(path)
print("Merge Folder: {0}".format(merge_folder))

if not os.path.exists("Manual_Reports_Names.txt"):
    with open("Manual_Reports_Names.txt", 'w+') as fp:
        pass

with open('Manual_Reports_Names.txt') as f:
    line = f.readlines()
    print("Lines from Manual_Reports_Names.txt: {0}".format(line))

# Merging reports to database one by one
for i in range(len(merge_folder)):

    # if report_name is already there in the Manual_Reports_Names file then, no need to append to database.
    if merge_folder[i]+"\n" in line:
        print("Report {0} already appended to database".format(merge_folder[i]))    
    
    # if report_name is not there in Manual_Reports_Names file then, we need to proceed with "append to database" steps
    else:
        # appending report_name to Manual_Reports_Names.txt
        with open("Manual_Reports_Names.txt", "a") as fp:
            fp.write(merge_folder[i] + '\n')

        with open("Manual_Reports_Names.txt", "r") as fp:
            print("Manual_Reports_Names file data after appending current report name: {0}".format(fp.readlines()))

        
        # appending path to report to manual_reports list
        manual_report_path = os.path.join(path, merge_folder[i])
        print("Current Manual Report Path: {0}".format(manual_report_path))
        
        manual_reports_numbers = []
        """
Manual Reports Numbers list 1: [['3473', '2']]
Manual Reports Numbers list 2: [[3473, 2]]
Workweek value: [3473]
Value split: [[3, 4, 7, 3]]
Active years list 1: [3]
Active years list 2: [2]
Active year value: [2022]
Workweek: [47]
Workday: [3]
Date Format String: 2022ww47.3
        """
        
        # Finding BIOS label name from the name
        manual_reports_numbers.append(re.findall(r'\d+',manual_report_path))             #read only BIOS label numbers from file names
        
        print("Manual Reports Numbers list 1: {0}".format(manual_reports_numbers))

        workweek_value = []
        for i in range(len(manual_reports_numbers)):
            for j in range(len(manual_reports_numbers[i])):
                manual_reports_numbers[i][j] = int(manual_reports_numbers[i][j])        
        
        print("Manual Reports Numbers list 2: {0}".format(manual_reports_numbers))

        for i in range(len(manual_reports_numbers)):
            workweek_value.append(max(manual_reports_numbers[i]))
	    
        print("Workweek value: {0}".format(workweek_value))

        value_split = []
        for i in range(len(workweek_value)):
            value_split.append([int(d) for d in str(workweek_value[i])])
	    
        print("Value split: {0}".format(value_split))

        active_years = []
        for i in range(len(value_split)):
            active_years.append(value_split[i][0])

        print("Active years list 1: {0}".format(active_years))

        active_year_value = []
        active_years = [x - 1 for x in active_years]
	    
        print("Active years list 2: {0}".format(active_years))

        for i in range(len(active_years)):
            active_year_value.append(int(first_year_value) + active_years[i])
	    
        print("Active year value: {0}".format(active_year_value))

        workweek = []
        for i in range(len(value_split)):
            workweek.append(int(str(value_split[i][1]) + str(value_split[i][2])))
	    
        print("Workweek: {0}".format(workweek))
        if workweek[0] in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] or workweek[0] in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            workweek[0] = "0" + str(workweek[0])

        workday = []
        for i in range(len(value_split)):
            workday.append(value_split[i][3])
	    
        print("Workday: {0}".format(workday))

        date_format_string = ""
        convert_date = []
        for i in range(len(workday)):
            date_format_string = f'{active_year_value[i]}ww{workweek[i]}.{workday[i]}'
	    
        print("Date Format String: {0}".format(date_format_string))

        label = re.findall(r'BAT',merge_folder[i]) 
        print("Label: {0}".format(label)) 

        
        dataframes = pd.read_excel(manual_report_path)                    #convert .xls/.xlsx to pandas dataframes
        
        print("Dataframes: {0}".format(dataframes))
        print(dataframes["TCD_ID"])
        print("First value: {0}".format(dataframes.iat[0,0]))
        print(dataframes.columns)
        dataframes['TCD_ID'] = dataframes['TCD_ID'].replace('', np.nan)                            
        dataframes = dataframes.dropna(axis=0, subset=['TCD_ID'])

        print("TCD_ID after dropping NaN:\n")
        print(dataframes["TCD_ID"])
        print(dataframes.shape)
        for idx, row_data in dataframes.iterrows():
            if str(dataframes.iat[idx, 0]).startswith("=HYPERLINK"):
                dataframes.iat[idx, 0] = int(str(dataframes.iat[idx, 0]).strip().split('=HYPERLINK("https://hsdes.intel.com/resource/')[1].split('","')[0])
            else:
                dataframes.iat[idx, 0] = int(float(str(dataframes.iat[idx, 0])))


        df_length = 0
        
        dataframes.columns = [x.lower() for x in dataframes.columns]
        df_length = len(dataframes.columns)                            #extract only column names
        print("DF Length: {0}".format(df_length))
        
        label_bat = re.findall(r'BAT', merge_folder[i])           #read only BIOS Plan from file names
        print("Label BAT: {0}\n".format(label_bat))

        if len(label_bat):
            if 'Test Plan' not in dataframes.columns:
                dataframes.insert(df_length, "Test Plan", table_names[args.p.lower()] + '_' + args.s.upper() + '_' + 'BAT')  #insert test plan in manual report column
                df_length += 1
            if 'Test Cycle' not in dataframes.columns:	
                dataframes.insert(df_length, "Test Cycle", args.p.lower() + '.milestone.BIOS.BAT_' + str(workweek_value[0])+'_00' )    #insert test cycle in manual report column
                df_length += 1
        
        label_bat = re.findall(r'Orange', merge_folder[i])           #read only BIOS Plan from file names
        print("Label BAT: {0}\n".format(label_bat))

        if len(label_bat):
            if 'Test Plan' not in dataframes.columns:
                dataframes.insert(df_length, "Test Plan", table_names[args.p.lower()] + '_' + 'ORANGE')  #for server programs insert test plan in manual report column
                df_length += 1
            if 'Test Cycle' not in dataframes.columns:	
                dataframes.insert(df_length, "Test Cycle", args.p.lower() + '.milestone.BIOS.ORANGE_' + str(workweek_value[0])+'_00' )    #for server programs insert test cycle in manual report column
                df_length += 1

        label_fv = re.findall(r'FV', merge_folder[i])           #read only FV Plan from file names
        print("Label FV: {0}\n".format(label_fv))

        if len(label_fv):
            for i in range(len(dataframes)):
                if 'Test Plan' not in dataframes.columns:
                    dataframes.insert(df_length, "Test Plan", table_names[args.p.lower()] + '_' + args.s.upper() + '_' + 'FV')  #insert test plan in manual report column
                    df_length += 1
                if 'Test Cycle' not in dataframes.columns:	
                    dataframes.insert(df_length, "Test Cycle", args.p.lower() + '.milestone.BIOS.FV_' + str(workweek_value[0])+'_00' )    #insert test cycle in manual report column
                    df_length += 1

        label_fv = re.findall(r'Blue', merge_folder[i])           #read only FV Plan from file names
        print("Label FV: {0}\n".format(label_fv))

        if len(label_fv):
            for i in range(len(dataframes)):
                if 'Test Plan' not in dataframes.columns:
                    dataframes.insert(df_length, "Test Plan", table_names[args.p.lower()] + '_' + 'BLUE')  #insert test plan in manual report column
                    df_length += 1
                if 'Test Cycle' not in dataframes.columns:	
                    dataframes.insert(df_length, "Test Cycle", args.p.lower() + '.milestone.BIOS.BLUE_' + str(workweek_value[0])+'_00' )    #insert test cycle in manual report column
                    df_length += 1

        """label_vs = re.findall(r'VS', merge_folder[i])           #read only VS Plan from file names
        print("Label VS: {0}\n".format(label_vs))

        if len(label_vs):
            if 'Test Plan' not in dataframes.columns:
                dataframes.insert(df_length, "Test Plan", table_names[args.p.lower()] + '_' + args.s.upper() + '_' + 'VS')  #insert test plan in manual report column
                df_length += 1
            if 'Test Cycle' not in dataframes.columns:	
                dataframes.insert(df_length, "Test Cycle", args.p.lower() + '.milestone.BIOS.VS_' + str(workweek_value[0])+'_00' )    #insert test cycle in manual report column
                df_length += 1"""

        if 'Execution Date' not in dataframes.columns:
            dataframes.insert(df_length, "Execution Date", date_format_string)   #insert Execution Date in manual report columns
            df_length += 1
    
        if 'TC ID' not in dataframes.columns:
            dataframes.insert(df_length, "TC ID", '9999999999')    #insert test case ID in manual report column
            df_length += 1

        if 'TC Title' not in dataframes.columns:
            dataframes.insert(df_length, "TC Title", dataframes['tcd_title'] + '_Test_Case')    #insert test case ID in manual report column
            df_length += 1
        
        if 'Release' not in dataframes.columns:
            dataframes.insert(df_length, "Release", args.p.lower())     #insert release affected in manual report column
            df_length += 1

        if 'TR ID' not in dataframes.columns:
            dataframes.insert(df_length, "TR ID", '9999999999')    #insert test result ID in manual report column
            df_length += 1

        if 'TR Title' not in dataframes.columns:
            dataframes.insert(df_length, "TR Title", dataframes['tcd_title'] + '_Test_Result')    #insert test result ID in manual report column
            df_length += 1


        print("Dataframes after adding columns: {0}".format(dataframes))
        print("Column Status: {0}".format(dataframes["status"]))
        print("Dataframes column: {0}".format(dataframes.columns))

        db_column_names = ['Test_Case_Definition_ID', 'Test_Case_Definition_Title', 'Test_Coverage_Level', 'Test_Case_ID', 'Test_Case_Title', 'Release_Affected', 'Test_Plan', 'Test_Result_ID', 'Test_Result_Title', 'Status_Reason', 'Test_Cycle', 'End_Date', 'Domain', 'Domain_Affected', 'Component', 'Component_Affected']

        # column_names = []
        # print("Dataframes ---------------------------------------------------------------------------------------------------------------")
        # print(dataframes) 
        # for i in range(len(dataframes)):
        #     print("Column names in loop")
        #     print(column_names)
        #     column_names.append(dataframes[i][['id','title','status', 'Test Plan','Execution Date', 'TC ID', 'TC Title', 'TR ID', 'TR Title', 'Release', 'Test Cycle']])    #merge manual report dataframes
        # print("Column names ------------------------------------------------------------------------------------------------------")
        # print(column_names)
        
        # dataframes.to_excel("output1.xlsx",index = False)                                            #merge and create excel file

        # dataframes = pd.read_excel("output1.xlsx")
        dataframes['tcd_title'] = dataframes['tcd_title'].replace('', np.nan)                            
        dataframes = dataframes.dropna(axis=0, subset=['tcd_title'])

        print("Dataframes TCD_ID column: {0}".format(dataframes["tcd_id"]))
        print("Dataframes TCD_Title column: {0}".format(dataframes["tcd_title"]))
        print("TCD Title cleared!")
        
        # column = ['tcd_id']
        # df2 = pd.read_excel("output1.xlsx", usecols = column)
        # print(df2['id'])

        print("Going to raise HTTP requests...")

        for j in range(len(dataframes)): 
            #if not pd.isna(dataframes.iloc[j, 0]):
            tcd_id = int(dataframes.at[j, "tcd_id"])
            print("Current_TCD_ID = {0}".format(tcd_id))
            url = 'https://hsdes-api.intel.com/rest/article/' + str(tcd_id)
            response = requests.get(url, verify = False, auth = HTTPKerberosAuth(), headers = headers)	
            print("Response = {0}".format(response))
            print("Response code = {0}".format(response.status_code))
            if (response.status_code == 200):
                data_rows = response.json()['data']
                #print(data_rows)
                print("Valid response got... creating new columns")
                for row in data_rows:
                    dataframes.at[j, 'Test_Coverage_Level'] = row['central_firmware.test_case_definition.test_coverage_level']
                    dataframes.at[j, 'Domain'] = row['domain']
                    dataframes.at[j, 'Domain_Affected'] = row['domain_affected']
                    dataframes.at[j, 'Component'] = row['component']
                    dataframes.at[j, 'Component_Affected'] = row['component_affected']		

        print("Changing status values...")

        dataframes['status']=dataframes['status'].replace(to_replace = 'Passed', value = 'complete.pass')
        dataframes['status']=dataframes['status'].replace(to_replace = 'complete.pass', value = 'complete.pass')
        dataframes['status']=dataframes['status'].replace(to_replace = 'complete', value = 'complete.pass')
        dataframes['status']=dataframes['status'].replace(to_replace = 'PASSED', value = 'complete.pass')
        dataframes['status']=dataframes['status'].replace(to_replace = 'passed', value = 'complete.pass')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Pass', value = 'complete.pass')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Fail', value = 'complete.fail')
        dataframes['status']=dataframes['status'].replace(to_replace = 'complete.fail', value = 'complete.fail')
        dataframes['status']=dataframes['status'].replace(to_replace = 'PASS', value = 'complete.pass')
        dataframes['status']=dataframes['status'].replace(to_replace = 'pass', value = 'complete.pass')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Failed', value = 'complete.fail')
        dataframes['status']=dataframes['status'].replace(to_replace = 'FAILED', value = 'complete.fail')
        dataframes['status']=dataframes['status'].replace(to_replace = 'failed', value = 'complete.fail')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Fail', value = 'complete.fail')
        dataframes['status']=dataframes['status'].replace(to_replace = 'fail', value = 'complete.fail')
        dataframes['status']=dataframes['status'].replace(to_replace = 'FAIL', value = 'complete.fail')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Block_Other', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Blocked', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'BLOCKED', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'blocked', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Block', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'block', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'NA', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Na', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'na', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'N/A', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'n/a', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'In-Progress', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'In Progress', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'inprogress', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Inprogress', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Inventory Block', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'inventory block', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Inventory block', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Inventory BLOCK', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'In/inpro', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Inventory Block ', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'inventory Block ', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'INVENTORY BLOCKED', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'blocked.feature_not_yet_enabled', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'blocked.missing_inventory', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'blocked.incorrect_configuration', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'blocked.awaiting_collateral', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'blocked.blocked_due_to_open_sighting', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'open.wip', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'NotRun', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Not run', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'Not_Run', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = ' ', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = '', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'WIP', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'wip', value = 'blocked.other')
        #dataframes['status']=dataframes['status'].replace(to_replace = 'Not Applicable', value = 'blocked.other')
        dataframes['status']=dataframes['status'].replace(to_replace = 'open', value = 'blocked.other')
        
        
        
        #dataframes=dataframes[dataframes["status"].str.contains(".not_run")==False]




        
        print("Renaming all columns...")

        dataframes=dataframes.rename(columns = {'tcd_id':'Test_Case_Definition_ID'})                         #rename column names to match with master list
        dataframes=dataframes.rename(columns = {'status':'Status_Reason'})                              
        dataframes=dataframes.rename(columns = {'tcd_title':'Test_Case_Definition_Title'}) 
        dataframes=dataframes.rename(columns = {'Test Plan':'Test_Plan'})                              
        dataframes=dataframes.rename(columns = {'Execution Date':'End_Date'})                               
        dataframes=dataframes.rename(columns = {'TC ID':'Test_Case_ID'})
        dataframes=dataframes.rename(columns = {'TC Title':'Test_Case_Title'})
        dataframes=dataframes.rename(columns = {'TR ID':'Test_Result_ID'})
        dataframes=dataframes.rename(columns = {'TR Title':'Test_Result_Title'})
        dataframes=dataframes.rename(columns = {'Release':'Release_Affected'})
        dataframes=dataframes.rename(columns = {'Test Cycle':'Test_Cycle'})

        print("Appending to database...")

        # conn = create_connection(os.path.join(os.getcwd( ), './DB/YBO_HSDES_TR_Database.db'))

        print(dataframes)
        dataframes[db_column_names].to_sql(table_name, db, if_exists='append', index=False)
        # os.remove("output1.xlsx")

        print("Appending to database done!")

        query = "UPDATE " + table_name + " SET Status_Reason = 'blocked.other' WHERE Status_Reason ISNULL"
        print("Update Null values query = {0}".format(query))
        c.execute(query)

        print("Null values updation done!")


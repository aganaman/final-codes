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


process_name="lnl_m_bios.json"
#test_plan="LNL_M_VS1_BIOS_eBAT_v1142.00_2022WW14"
string= "bios.arrowlake.PSS-1.0.Client-BIOS.S_Security_Ext-BAT_2314_22WW31.1_test-cycle#01"
owner_team="client-bios"
#
global pg_list
pg_list=process_name.split("_")

mapping_dict={
    "pg_name":{
        "mtl":"meteorlake",
        "rpl":"raptorlake",
        "lnl":"lunarlake",
        "arl":"arrowlake",
        "adl":"alderlake"
    },
    "platform_name" : ['mtl','lnl','rpl','arl','adl','gnr','spr','usf','tgl','cfl','egs','gnr'],
    "sku":["m","p","s","ap","sp","r1s","qsp","sbga","n"],
    "milestone":['ip-efv', 'ip-ev1', 'ip-ev2', 'ip-fv', 'ip-uv', 'ip-uv1', 'ip-uv2', 'product-concept', 'engineering-commit', 'rtl-0p3', 
                 'rtl-0p5', 'rtl-0p8', 'rtl-1p0', 'rtl-1p1', 'pss-0p3', 'pss-0p5', 'pss-0p8', 'pss-1p0', 'pss-1p1', 'ppo', 'tape-in', 'power-on', 
                 'pre-alpha', 'es1', 'es2', 'alpha', 'beta', 'qs', 'product-candidate', 'product-version', 'prq', 'sustaining', 'po-phase0', 'po-phase1', 
                 'po-phase2', 'po-phase3', 'vs0', 'vs1','pss1.0','pss0.8'],
    "charter":['tr-mrc', 'nt-mrc', 'fweval', 'emu', 'sdl', 'ppo', 'ifwi', 'security', 'hlk', 'acm', 'clv', 'ipval-uncore', 'ipval-ras', 
                'ipval-mrc', 'usf', 'bios', 'sciv'],
    "test_coverage_level":["bl","or","sanity","ebat","bat","ext-bat","fv","per-milestone",'vs',"orange","blue"],
    "owner_team":["server-bios", "server-ifwi", "client-bios", "client-ifwi"],
}

import re


#string="LNL_M_VS1_BIOS_eBAT_v1282.00_2022WW28"

#format check for test plan
def match_string_test_plan(string):
    pattern = re.compile(r'(?P<platform_name>[A-Za-z0-9]{3,5})_(?P<sku>[a-zA-Z0-9-]{1,5})_(?P<milestone>[a-zA-Z0-9-.]+)_(?P<charter>[a-zA-Z0-9-]{1,12})_(?P<test_coverage_level>[a-zA-Z0-9-]{1,14})')
    match = pattern.match(string)
    if match:
        platform_name = match.group('platform_name').lower()
        sku = (match.group('sku')).lower()
        milestone = (match.group('milestone')).lower()
        charter = (match.group('charter')).lower()
        test_coverage_level = (match.group('test_coverage_level')).lower()
        print(platform_name,sku,milestone,charter,test_coverage_level)
        if platform_name in mapping_dict['platform_name'] and sku in mapping_dict['sku'] and milestone in mapping_dict['milestone'] and charter in mapping_dict['charter'] and test_coverage_level in mapping_dict['test_coverage_level']:
            print(f"Accepted: {string}")
            return True
        else:
            print(f" in inner if Rejected: {string}")
            return False
    else:
        print(f"Rejected: {string}")
        return False
"""
def match_string_test_cycle(string):
    
    pattern = re.compile(r'(?P<release_1>[A-Za-z]{4})\.(?P<release_2>[A-Za-z_]+)\.(?P<milestone>[a-zA-Z0-9-]+)\.(?P<owner_team>[a-zA-Z-]+)\.(?P<sku>[a-zA-Z0-9-]{1,5})_(?P<charter>[a-zA-Z0-9-]{1,12})_(?P<test_coverage_level>[a-zA-Z0-9-]{1,14})_(?P<version>[a-zA-Z0-9-\.]+)_(\d{2}WW\d{2}\.\d)_(?P<test_cycle_no>[a-zA-Z0-9#-\.]+)')
    match = pattern.match(string)
    if match:
        release_1 = match.group('release_1').lower()
        release_2 = match.group('release_2').lower()
        milestone = (match.group('milestone')).lower()
        owner_team = (match.group('owner_team')).lower()
        sku = (match.group('sku')).lower()
        charter = (match.group('charter')).lower()
        test_coverage_level = (match.group('test_coverage_level')).lower()
        version = (match.group('version')).lower()
        #testcycle_time = (match.group('testcycle_time')).lower()
        test_cycle_no = (match.group('test_cycle_no')).lower()
        
        if pg_list[2].split(".")[0] == release_1 and mapping_dict["pg_name"][pg_list[0]] and milestone in mapping_dict['milestone'] and owner_team in mapping_dict['owner_team'] and sku in mapping_dict['sku'] and sku == pg_list[1].lower() and charter in mapping_dict['charter'] and test_coverage_level in mapping_dict['test_coverage_level']:
            print(f"Accepted: {string}")
            print(release_1, release_2, milestone, owner_team, sku, charter, test_coverage_level, version, test_cycle_no)
            return True
        else:
            print(f" in inner if Rejected: {string}")
            return False
    else:
        print(f"Rejected: {string}")
        return False
"""

#bios.arrowlake.PSS-1.0.Client-BIOS.S_Security_Ext-BAT_2314_22WW31.1_test-cycle#01

def match_string_test_cycle(string):

    list_dot=[]
    list_dot=string.split("_")
    list_underscore=[]
    list_underscore=list_dot[0].split(".")
    print(list_dot,list_underscore,list_underscore[-1].lower())
    if list_underscore[-1].lower() == pg_list[1].lower() and list_underscore[-2].lower() == owner_team:
        print("Accepted")
        return True
    else:
        print("Rejected")
        return False


#test plan generation for a project
def generate_test_plan():
    pg_list=process_name.split("_")
    if pg_list[2].split(".")[0]=="security":
        release_aff="bios"+"."+mapping_dict["pg_name"][pg_list[0]]
    else:
        release_aff=pg_list[2].split(".")[0]+"."+mapping_dict["pg_name"][pg_list[0]]
    #start_str=LNL_M
    start_str=pg_list[0].upper()+"_"+pg_list[1].upper()
    eql_test_case_definitions = "\"eql\":\"select id, title , submitted_date where " \
                        "tenant='central_firmware' and subject='test_plan' and release_affected contains '{0}' and title contains '{1}'" \
                        "\"".format(release_aff,start_str)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
    resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
    if resp.status_code == 200:
        test_results_data = resp.json()['data']
        #print(test_results_data)
    else:
        print(resp.status_code)

    #print("---------------------------------------------------------------------------------------------------------------")
    sorted_test_results_data=sorted(test_results_data, key=lambda x: x['submitted_date'], reverse=True)
    #print(sorted_test_results_data)
    title_test_plan=[]
    for row in sorted_test_results_data:
        title_test_plan.append((row['title'].split('[')[0].strip()))
    #title1=list(set(title))
    result=[]
    #print(title1)
    if "security" in process_name:
        result=[x for x in title_test_plan if "Security" in x]
    else:
        result=title_test_plan
    #print("Before calling the string match function: ",len(result))
    global final_test_plan
    final_test_plan=[]
    for i in result:
        if match_string_test_plan(i):
            final_test_plan.append(i)

    print("After applying string matcg func :",len(final_test_plan))
    print("--------------------------------------------------------------------------------------------------")
    print(final_test_plan)


#test_cycle generation for project
def generate_test_cycle():
    pg_list=process_name.split("_")
    if pg_list[2].split(".")[0]=="security":
        release_aff="bios"+"."+mapping_dict["pg_name"][pg_list[0]]
    else:
        release_aff=pg_list[2].split(".")[0]+"."+mapping_dict["pg_name"][pg_list[0]]
    #start_str=LNL_M
    eql_test_case_definitions = "\"eql\":\"select id, title , submitted_date where " \
                        "tenant='central_firmware' and subject='milestone' and release contains '{0}'" \
                        "\"".format(release_aff)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
    resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
    if resp.status_code == 200:
        test_cycle_data = resp.json()['data']
        #print(test_results_data)
    else:
        print(resp.status_code)

    #print("---------------------------------------------------------------------------------------------------------------")
    sorted_test_cycle_data=sorted(test_cycle_data, key=lambda x: x['submitted_date'], reverse=True)
    #print(sorted_test_results_data)
    title_test_cycle=[]
    for row in sorted_test_cycle_data:
        title_test_cycle.append((row['title'].split('[')[0].strip()))
    #title1=list(set(title))
    result=[]
    #print(title1)
    if "security" in process_name:
        result=[x for x in title_test_cycle if "Security" in x]
    else:
        result=title_test_cycle
    #print("Before calling the string match function: ",len(result))
    global final_test_cycle
    final_test_cycle=[]
    for i in result:
        if match_string_test_cycle(i):
            final_test_cycle.append(i)

    print("After applying string matcg func :",len(final_test_cycle))
    print("--------------------------------------------------------------------------------------------------")
    print(final_test_cycle)
    print(len(result))

#generate_test_cycle()
#match_string_test_cycle(string)


#config for all test plan (test plan unselected)
def generate_configuration():
    pg_list=process_name.split("_")
    if pg_list[2].split(".")[0]=="security":
        release_aff="bios"+"."+mapping_dict["pg_name"][pg_list[0]]
    else:
        release_aff=pg_list[2].split(".")[0]+"."+mapping_dict["pg_name"][pg_list[0]]
    
    eql_test_case_definitions = "\"eql\":\"select id, status, config_version.version, submitted_date where " \
                        "tenant='central_firmware' and subject='config_version' and release contains '{0}'" \
                        "\"".format(release_aff)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
    resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
    if resp.status_code == 200:
        test_results_data = resp.json()['data']
        #print(test_results_data)
    else:
        print(resp.status_code)

    sorted_test_results_data=sorted(test_results_data, key=lambda x: x['submitted_date'], reverse=True)
    #print(sorted_test_results_data)
    version=[]
    for row in sorted_test_results_data:
        version.append((row['config_version.version'].split('[')[0].strip()))
    print(version)
    print(len(version))


#config for test_plan selected (when test plan is selected)
def generate_tp_config(test_plan):
    pg_list=process_name.split("_")
    if pg_list[2].split(".")[0]=="security":
        release_aff="bios"+"."+mapping_dict["pg_name"][pg_list[0]]
    else:
        release_aff=pg_list[2].split(".")[0]+"."+mapping_dict["pg_name"][pg_list[0]]
    
    eql_test_case_definitions = "\"eql\":\"select id, central_firmware.test_case.configuration, submitted_date where " \
                        "tenant='central_firmware' and subject='test_case' and release_affected contains '{0}' and central_firmware.test_case.planned_for contains '{1}'" \
                        "\"".format(release_aff,test_plan)

    payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
    resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
    if resp.status_code == 200:
        test_results_data = resp.json()['data']
        print(test_results_data)
    else:
        print(resp.status_code)

    sorted_test_results_data=sorted(test_results_data, key=lambda x: x['submitted_date'], reverse=True)
    #print(sorted_test_results_data)
    version=[]
    for row in sorted_test_results_data:
        version.append((row['central_firmware.test_case.configuration'].split('[')[0].strip()))
    print("Plan Name--{0} and len of Configurations--{1}".format(test_plan,list(set(version))))
    print(len(list(set(version))))
    #print(version)




generate_test_plan()
#generate_configuration()
#generate_tp_config("LNL_M_VS0_Security_FV_V1142.00_2022WW15")
for i in final_test_plan:
    generate_tp_config(i)








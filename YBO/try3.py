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

eql_test_case_definitions = "\"eql\":\"select release_affected where " \
                       "tenant='central_firmware' and subject='test_plan' " \
                       "\""

payload_eql_tcds = """{""" + """{0}""".format(eql_test_case_definitions) + """}"""
resp = requests.post(url=base_url,data = payload_eql_tcds, verify = False, auth = HTTPBasicAuth(username, password), headers = headers)
if resp.status_code == 200:
    test_results_data = resp.json()['data']
    #print(test_results_data)
else:
    print(resp.status_code)

rel=[]
for row in test_results_data:
    rel.append(row["release_affected"])
print(list(set(rel)))
print(len(list(set(rel))))
import pandas as pd
import sqlite3

test_case_definition_id = []
test_case_definition_title = []
test_coverage_level = []
test_case_id = []
test_case_title = []
test_case_result_id = []
status_reason = []
actual_end = []
release_affected = []
test_plan = []
test_cycle = []

def get_test_case_definition_id(data, column_names):
    for item in data:
        test_case_definition_id.append(item[column_names.index('Test_Case_Definition_ID')])
    return test_case_definition_id

def get_test_case_definition_title(data, column_names):
    for item in data:
        test_case_definition_title.append(item[column_names.index('Test_Case_Definition_Title')])
    return test_case_definition_title

def get_test_coverage_level(data, column_names):
    for item in data:
        test_coverage_level.append(item[column_names.index('Test_Coverage_Level')])
    return test_coverage_level

def get_test_case_id(data, column_names):
    for item in data:
        test_case_id.append(item[column_names.index('Test_Case_ID')])
    return test_case_id

def get_test_case_title(data, column_names):
    for item in data:
        test_case_title.append(item[column_names.index('Test_Case_Title')])
    return test_case_title

def get_test_result_id(data, column_names):
    for item in data:
        test_case_result_id.append(item[column_names.index('Test_Result_ID')])
    return test_case_result_id

def get_status_reason(data, column_names):
    for item in data:
        status_reason.append(item[column_names.index('Status_Reason')])
    return status_reason

def get_actual_end(data, column_names):
    for item in data:
        actual_end.append(item[column_names.index('End_Date')])
    return actual_end

def get_release_affected(data, column_names):
    for item in data:
        release_affected.append(item[column_names.index('Release_Affected')])
    return release_affected

def get_test_plan(data, column_names):
    for item in data:
        test_plan.append(item[column_names.index('Test_Plan')])
    return test_plan

def get_test_cycle(data, column_names):
    for item in data:
        test_cycle.append(item[column_names.index('Test_Cycle')])
    return test_cycle
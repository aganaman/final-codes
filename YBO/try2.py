import pandas as pd
import json
import sqlite3

with open("C:/NAMAN/Share/YBO/ybo_config.json") as json_data_file:
	json_data = json.load(json_data_file)
db_name = json_data["config"]["db_name"]
print(db_name)


db = sqlite3.connect("./DB/" + db_name)
print(db)
c = db.cursor()

table_name="RPL_S"
program_name="bios.andersonlake"

df_new = pd.DataFrame(columns = ["Test_Case_Definition_ID", "Test_Case_Definition_Title", "Test_Coverage_Level", "Test_Case_ID",
                            "Test_Case_Title","Release_Affected", "Test_Plan", "Test_Result_ID",
                            "Test_Result_Title", "Status_Reason", "Test_Cycle", "End_Date", "Domain", "Domain_Affected",
                            "Component", "Component_Affected"])
df1 = pd.read_sql_query("SELECT * FROM {0}".format(table_name), db)
print(df1)
unique_tcd=df1["Test_Case_Definition_ID"].unique()
for tcd in unique_tcd:
    df=df1[df1["Test_Case_Definition_ID"]==tcd]
    df = df.sort_values(by = "End_Date", ascending=False)
    end_date = df.iloc[0,11]
    print("end_date : ",end_date)
    date = str(end_date)
    x = date.split(".")
    work_day = x[1]
    y = x[0].split("ww")
    #y1 = y[0].split(" ")
    y2 = y[0]
    ww = int(y[1])
    new_ww = ww - 25
    if (new_ww > 0):
        work_week = new_ww
        year = y2
    elif(new_ww <= 0):
        work_week = 52 + new_ww
        year = int(y2) -1

    date = str(year) +'ww'+ str(work_week) +'.'+ str(work_day)
    print(date)
    
    df.drop(df[(df['End_Date'] <= date)].index, inplace=True)
    print(df)
        
    df_new=pd.concat([df_new,df],ignore_index=True)  
    
df_new["Release_Affected"]=program_name
df_new.to_sql(table_name, db, if_exists = 'replace', index = False)
    
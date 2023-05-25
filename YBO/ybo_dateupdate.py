import sqlite3
from sqlite3 import Error
import argparse
import os
import logging
import json
import pandas as pd

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

db = sqlite3.connect("./DB/" + db_name)
print(db)
c = db.cursor() 

df = pd.read_sql_query("SELECT * FROM {0}".format(table_name), db)
print(df)
df = df.sort_values(by = "End_Date", ascending=False)
print(df)
end_date = df.iloc[0:1,11:12]
print(end_date)
date = str(end_date)
x = date.split(".")
work_day = x[1]
print(work_day)
y = x[0].split("ww")
print(y)
y1 = y[0].split(" ")
print(y1)
y2 = y1[10]
ww = int(y[1])
print(work_day)
print(ww)

new_ww = ww - 24
if (new_ww > 0):
    work_week = new_ww
    year = y2
elif(new_ww < 0):
    work_week = 52 + new_ww
    year = int(y2) -1
print(year)
print(work_week)

date = str(year) +'ww'+ str(work_week) +'.'+ str(work_day)
print(date)
df.drop(df[(df['End_Date'] <= date)].index, inplace=True)
print(df)
df.to_sql(table_name, db, if_exists = 'replace', index = False)
print("All Done!!!")
# df.to_sql(table_name, db, if_exists = 'replace', index = False)
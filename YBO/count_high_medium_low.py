import pandas as pd
path=r"C:\NAMAN\Share\YBO\Savings\RPL-Hx_BIOSv3441_01_99_Ext_BAT_Validation Results.xlsx"
#dataframes = pd.read_csv(path)    
dataframes = pd.read_excel(path)    
high=0
low=0
medium=0
print(dataframes)
for idx, row_data in dataframes.iterrows():
            if str(dataframes.iat[idx, 7])=="High":
                high+=1
            elif str(dataframes.iat[idx,7])=="Medium":
                medium+=1
            else:
                low+=1
print("HIGH : ",high)
print("MEDIUM :",medium)
print("LOW :",low)

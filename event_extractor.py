import numpy as np
import pandas as pd
from datetime import datetime
import uuid
import os
class xlsxtocsv():

    def get_data(self, filename, skiprowsnr):
        data = pd.read_excel(filename, skiprows=skiprowsnr)
        return data

    def rename_columns(self, data):
        old_columns = data.columns
        j = 0
        if j == 0:
            new_columns = ['DATE', 'TIME', 'SL_PJ_PRESSURE', 'SL_PJ_TEMPERATURE', 'SL_OP_HOIST-DEPTH', 'SL_OP_HOIST-SPEED', 'COMMENT']
        for i in range(len(old_columns)):
            data.rename(columns={old_columns[i]: new_columns[i]}, inplace=True)
        return data

    def create_timestamp(self, data):
        timestamp = []
        for i in range(0, len(data['TIME'])):
            timestamp.append(
                data['DATE'].iloc[i].strftime("%Y-%m-%d") + 'T' + data['TIME'].iloc[i].strftime(
                    "%H:%M:%S") + '.000-05:00')
        return timestamp

    def create_uid(self, data):
        uid = []
        for i in range(0, data.shape[0]):
            uid.append(str(uuid.uuid1()))
        return uid

    def filter_comment(self, data):
        filtered_data = data[data['COMMENT'].notnull()]
        return filtered_data

    def export_to_csv(self, data, timestamp):
        export_data = pd.DataFrame()

    def add_units(self, data):
        data.loc[-1] = ['m', 'sec', 'kg']  # adding a row
        data.index = data.index + 1  # shifting index
        data.sort_index(inplace=True)


filename = 'Log report.xlsx'
skiprowsnr = 0
data = xlsxtocsv().get_data(filename, skiprowsnr)
# data = xlsxtocsv().rename_columns(data)
# filtered_data = xlsxtocsv().filter_comment(data)
filtered_data = data
# timestamp = xlsxtocsv().create_timestamp(filtered_data)
uid = xlsxtocsv().create_uid(filtered_data)


export_data = pd.DataFrame()
# OPTION 1
# export_data["UID"] = uid
# export_data["Name"] = uid
# export_data["Type Message"] = 'informational'
# export_data["Time"] = timestamp
# export_data["Md"] = ""
# export_data["uom"] = 'm'
# export_data["Md bit"] = filtered_data['SL_OP_HOIST-DEPTH'].reset_index(drop=True)
# export_data["md"] = 'm'
# export_data["Activity Code"] = ""
# export_data["Detail Activity"] = ""
# export_data["Message"] = filtered_data['COMMENT'].reset_index(drop=True)
# export_data.to_csv("Log report.csv", index=False)

# OPTION 2
export_data["UID"] = uid
export_data["Name"] = uid
export_data["Type Message"] = 'informational'
export_data["Time"] = data['Time']
export_data["Md"] = ""
export_data["uom"] = 'm'
export_data["Md bit"] = ''
export_data["md"] = 'm'
export_data["Activity Code"] = ""
export_data["Detail Activity"] = ""
export_data["Message"] = data['Message']
export_data.to_csv("Log report.csv", index=False)



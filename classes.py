import json
import os
from bs4 import BeautifulSoup
import re
import statistics
from datetime import datetime, date
from xml.dom import minidom
from xml.etree.ElementTree import tostring, SubElement, Element, ElementTree
import plotly
import plotly.graph_objs as go
from plotly import subplots
import pandas as pd
from tabulate import tabulate


class Configuration:
    """Configurations"""

    def serviceTypeOptions(self):
        file = open('configuration/service type.txt')
        choices = []
        servicetype = []
        i = 0
        for line in file:
            index = line.find('\n')
            line1 = line[:index]
            servicetype.append(line1.split(' : '))
            choices.append((servicetype[i][1], servicetype[i][0]))
            i += 1
        return servicetype, choices

    def serviceTypeOptionsforXML(self):
        file = open('configuration/service type for XML.txt')
        choices = []
        servicetype = []
        i = 0
        for line in file:
            index = line.find('\n')
            line1 = line[:index]
            servicetype.append(line1.split(' : '))
            choices.append((servicetype[i][1], servicetype[i][0]))
            i += 1
        return servicetype, choices

    def dataTypeOptions(self):
        file = open('configuration/data type.txt')
        choices = []
        datatype = []
        i = 0
        for line in file:
            index = line.find('\n')
            line1 = line[:index]
            datatype.append(line1.split(' : '))
            choices.append((datatype[i][1], datatype[i][0]))
            i += 1
        return datatype, choices

    def KDIunits(self):
        dataframe1 = pd.read_excel('configuration/KDIunits.xlsx', index_col=0)
        dataframe1.columns = ['Units', 'Description']
        return dataframe1

    pass


class IndexType:
    """Functions to find index, index curve"""

    def findindex(self, file, type1):
        # determine indexes [depth, time] for visualization only
        index1 = None
        index2 = None
        if type1 == 'las':
            for curve in file.curves:
                if str(curve.mnemonic).lower().find(r'tim') != -1:
                    index1 = 'Time'
                elif str(curve.mnemonic).lower().find(r'dep') != -1:
                    index2 = 'Depth'
        elif type1 == 'csv':
            for col in file.columns:
                if str(col).lower().find(r'tim') != -1:
                    index1 = 'Time'
                elif str(col).lower().find(r'dept') != -1:
                    index2 = 'Depth'
        elif type1 == 'dlis':
            f = file
            indextype = []
            for frame in f.frames:
                indextype.append(frame.index_type)

            indexset = set(indextype)
            indextype1 = list(indexset)

            for each in indextype1:
                if str(each).lower().find(r'tim') != -1:
                    index1 = 'Time'
                elif str(each).lower().find(r'dept') != -1:
                    index2 = 'Depth'
        elif type1 == 'xml':
            Bs_data = BeautifulSoup(file, "xml")
            line1 = Bs_data.find_all('indexType')
            line0 = []
            for row in line1:
                line0.append(row.get_text())
            line = str(line0[0])
            if line.lower().find(r'tim') != -1:
                index1 = 'Time'
            elif line.lower().find(r'dep') != -1:
                index2 = 'Depth'
        if index1 is not None and index2 is not None:
            indextype = index1 + ', ' + index2
        elif index1 is not None:
            indextype = index1
        elif index2 is not None:
            indextype = index2
        else:
            indextype = 'Not found'
        return indextype, index1, index2

    def LASmnemonic(self, indextype, lf):
        # find index curve in LAS
        if indextype == 'Time':
            j = 0
            for curve in lf.curves:
                if str(curve['mnemonic']).find(r'ETIM') != -1:
                    timemnem = curve['mnemonic']
                    j += 1
            if j == 0:
                for curve in lf.curves:
                    if str(curve['mnemonic']).find(r'TIM') != -1:
                        timemnem = curve['mnemonic']
                        break
            return timemnem
        elif indextype == 'Depth':
            for curve in lf.curves:
                if str(curve['mnemonic']).lower().find(r'dep') != -1:
                    depthmnem = curve['mnemonic']
            return depthmnem

    def CSVindex(self, df2):
        # find csv index type
        for col in df2.columns:
            if col.lower().find('dept') != -1:
                indexType = 'measured depth'
                break
            elif col.lower().find('time') != -1:
                indexType = 'date time'
                break
        return indexType

    pass


class InputXMLprocessing:

    def curvesnumber(self, data1):
        Bs_data = BeautifulSoup(data1, "xml")
        line1 = Bs_data.find_all('mnemonicList')
        line0 = []
        for row in line1:
            line0.append(row.get_text())
        line = str(line0[0])
        index = line.find('>')
        index1 = line[index + 1:].find('<')
        indextype = line[index + 1:index + 1 + index1]
        curvesnumber = len(indextype.split(','))
        return curvesnumber

    def dataframeFromXml(self, data1):
        Bs_data = BeautifulSoup(data1, "xml")
        line1 = Bs_data.find_all('mnemonicList')
        line2 = Bs_data.find_all('unitList')
        line0 = []
        for row in line1:
            line0.append(row.get_text())
        line01 = []
        for row in line2:
            line01.append(row.get_text())
        line = str(line0[0])
        mnem = line.split(',')
        line = str(line01[0])
        units = line.split(',')
        curves = []
        i = 0
        for each in mnem:
            string = each + ' ' + units[i]
            curves.append(string)
            i += 1
        for curve in curves:
            curve = curve.strip()

        line1 = Bs_data.find_all('data')
        line0 = []
        for row in line1:
            line0.append(row.get_text())

        datablock = []
        for line in line0:
            x = line.split(',')
            datablock.append(x)

        df = pd.DataFrame(data=datablock, columns=curves)
        return df

    pass


class DLISprocessing:
    """Functions to process DLIS file"""

    def dlisInfo(self, f):
        # dlis summary
        indextype = []
        operation = []
        channelsnumber = 0

        for frame in f.frames:
            indextype.append(frame.index_type)
            operation.append(frame.direction)
            channelsnumber += int(len(frame.channels))

        indexset = set(indextype)
        indextype1 = list(indexset)
        operationset = set(operation)
        operation1 = list(operationset)
        ops = []
        for op in operation1:
            if op == 'DECREASING':
                ops.append('POOH')
            else:
                ops.append('RIH')
        return indextype1, channelsnumber, ops

    pass


class LASprocessing:
    def splitlogs(self, lf, repr):
        df0 = lf.df()
        df1 = df0
        for col in df0.columns:
            if str(col).lower().find(r'tim') != -1:
                coltime = col
                df1 = df1.drop(col, axis=1)
                pass

        df1 = df1.reset_index()
        RIH = []
        POOH = []
        index1 = 0
        index2 = 0
        for col in df1.columns:
            if str(col).lower().find(r'dept') != -1:
                col1 = col
        for i in range(len(df1)):
            if i != 0 and i != len(df1) - 1:
                if df1[col1].iloc[i - 1] < df1[col1].iloc[i] < df1[col1].iloc[i + 1]:
                    RIH.append(df1.iloc[i].tolist())
                    index1 += 1
                elif df1[col1].iloc[i - 1] > df1[col1].iloc[i] > df1[col1].iloc[i + 1]:
                    POOH.append(df1.iloc[i].tolist())
                    index2 += 1
                elif df1[col1].iloc[i - 1] < df1[col1].iloc[i] > df1[col1].iloc[i + 1] or df1[col1].iloc[
                    i - 1] > \
                        df1[col1].iloc[i] < df1[col1].iloc[i + 1]:
                    RIH.append(df1.iloc[i].tolist())
                    index1 += 1
                    POOH.append(df1.iloc[i].tolist())
                    index2 += 1
                elif df1[col1].iloc[i - 1] != df1[col1].iloc[i] and df1[col1].iloc[i] == df1[col1].iloc[i + 1]:
                    j1 = i
                elif df1[col1].iloc[i - 1] == df1[col1].iloc[i] and df1[col1].iloc[i] != df1[col1].iloc[i + 1]:
                    j2 = i
                    if j1 != 0:
                        RIH.append([])
                        for col in df1.columns:
                            if repr == 'mean':
                                RIH[index1].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'min':
                                RIH[index1].append(min(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'max':
                                RIH[index1].append(max(df1[col].iloc[j1:j2 + 1]))
                        index1 += 1
                        POOH.append([])
                        for col in df1.columns:
                            if repr == 'mean':
                                POOH[index2].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'min':
                                POOH[index2].append(min(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'max':
                                POOH[index2].append(max(df1[col].iloc[j1:j2 + 1]))
                        index2 += 1

                    else:
                        if df1[col1].iloc[i] < df1[col1].iloc[i + 1]:
                            RIH.append([])
                            for col in df1.columns:
                                if repr == 'mean':
                                    RIH[index1].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                                elif repr == 'min':
                                    RIH[index1].append(min(df1[col].iloc[j1:j2 + 1]))
                                elif repr == 'max':
                                    RIH[index1].append(max(df1[col].iloc[j1:j2 + 1]))

                            index1 += 1
                        else:
                            POOH.append([])
                            for col in df1.columns:
                                if repr == 'mean':
                                    POOH[index2].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                                elif repr == 'min':
                                    POOH[index2].append(min(df1[col].iloc[j1:j2 + 1]))
                                elif repr == 'max':
                                    POOH[index2].append(max(df1[col].iloc[j1:j2 + 1]))
                            index2 += 1
            elif i == 0:
                if df1[col1].iloc[i] < df1[col1].iloc[i + 1]:
                    RIH.append(df1.iloc[i].tolist())
                    index1 += 1
                elif df1[col1].iloc[i] > df1[col1].iloc[i + 1]:
                    POOH.append(df1.iloc[i].tolist())
                    index2 += 1
                else:
                    j1 = 0
            elif i == len(df1) - 1:
                if df1[col1].iloc[i] > df1[col1].iloc[i - 1]:
                    RIH.append(df1.iloc[i].tolist())
                elif df1[col1].iloc[i] < df1[col1].iloc[i - 1]:
                    POOH.append(df1.iloc[i].tolist())
                else:
                    j2 = i
                    if df1[col1].iloc[j1 - 1] > df1[col1].iloc[j1]:
                        POOH.append([])
                        for col in df1.columns:
                            if repr == 'mean':
                                POOH[index2].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'min':
                                POOH[index2].append(min(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'max':
                                POOH[index2].append(max(df1[col].iloc[j1:j2 + 1]))
                    else:
                        RIH.append([])
                        for col in df1.columns:
                            if repr == 'mean':
                                RIH[index1].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'min':
                                RIH[index1].append(min(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'max':
                                RIH[index1].append(max(df1[col].iloc[j1:j2 + 1]))

        if len(RIH) != 0:
            RIH = RIH[:RIH.index(max(RIH)) + 1]
        if len(POOH) != 0:
            POOH = POOH[POOH.index(max(POOH)):]

        # if df0[coltime].iloc[0] > df0[coltime].iloc[1]:
        #     RIH1 = RIH
        #     RIH = POOH
        #     POOH = RIH1
        return RIH, POOH

    pass


class CSVprocessing:
    """Functions to process CSV file"""

    def csvpreprocess(self, df0):
        # formatting csv for visualization
        df1 = pd.DataFrame()
        # drop empty columns
        for col in df0.columns:
            if df0[col].isnull().sum() != len(df0[col]):
                df1[col] = df0[col]
        # delete error cells
        for col in df1.columns:
            for i in range(len(df1[col])):
                if df1[col].iloc[i] == '-99999.99' or df1[col].iloc[i] == '-999.25':
                    df1[col].iloc[i] = None
        # drop NaNs
        df1 = df1.dropna(thresh=2)
        df1 = df1.reset_index(drop=True)
        return df1

    def splitlogs(self, df1, repr):

        for col in df1.columns:
            if str(col).lower().find(r'tim') != -1:
                df1 = df1.drop(col, axis=1)
                pass

        df1 = df1.reset_index(drop=True)
        df1 = self.csvnumeric(df1)
        RIH = []
        POOH = []
        index1 = 0
        index2 = 0
        for col in df1.columns:
            if str(col).lower().find('depth') != -1:
                col1 = col
        for i in range(len(df1)):
            if i != 0 and i != len(df1) - 1:
                if df1[col1].iloc[i - 1] < df1[col1].iloc[i] < df1[col1].iloc[i + 1]:
                    RIH.append(df1.iloc[i].tolist())
                    index1 += 1
                elif df1[col1].iloc[i - 1] > df1[col1].iloc[i] > df1[col1].iloc[i + 1]:
                    POOH.append(df1.iloc[i].tolist())
                    index2 += 1
                elif df1[col1].iloc[i - 1] < df1[col1].iloc[i] > df1[col1].iloc[i + 1] or df1[col1].iloc[
                    i - 1] > \
                        df1[col1].iloc[i] < df1[col1].iloc[i + 1]:
                    RIH.append(df1.iloc[i].tolist())
                    index1 += 1
                    POOH.append(df1.iloc[i].tolist())
                    index2 += 1
                elif df1[col1].iloc[i - 1] != df1[col1].iloc[i] and df1[col1].iloc[i] == df1[col1].iloc[i + 1]:
                    j1 = i
                elif df1[col1].iloc[i - 1] == df1[col1].iloc[i] and df1[col1].iloc[i] != df1[col1].iloc[i + 1]:
                    j2 = i
                    if j1 != 0:
                        RIH.append([])
                        for col in df1.columns:
                            if repr == 'mean':
                                RIH[index1].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'min':
                                RIH[index1].append(min(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'max':
                                RIH[index1].append(max(df1[col].iloc[j1:j2 + 1]))
                        index1 += 1
                        POOH.append([])
                        for col in df1.columns:
                            if repr == 'mean':
                                POOH[index2].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'min':
                                POOH[index2].append(min(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'max':
                                POOH[index2].append(max(df1[col].iloc[j1:j2 + 1]))
                        index2 += 1

                    else:
                        if df1[col1].iloc[i] < df1[col1].iloc[i + 1]:
                            RIH.append([])
                            for col in df1.columns:
                                if repr == 'mean':
                                    RIH[index1].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                                elif repr == 'min':
                                    RIH[index1].append(min(df1[col].iloc[j1:j2 + 1]))
                                elif repr == 'max':
                                    RIH[index1].append(max(df1[col].iloc[j1:j2 + 1]))

                            index1 += 1
                        else:
                            POOH.append([])
                            for col in df1.columns:
                                if repr == 'mean':
                                    POOH[index2].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                                elif repr == 'min':
                                    POOH[index2].append(min(df1[col].iloc[j1:j2 + 1]))
                                elif repr == 'max':
                                    POOH[index2].append(max(df1[col].iloc[j1:j2 + 1]))
                            index2 += 1
            elif i == 0:
                if df1[col1].iloc[i] < df1[col1].iloc[i + 1]:
                    RIH.append(df1.iloc[i].tolist())
                    index1 += 1
                elif df1[col1].iloc[i] > df1[col1].iloc[i + 1]:
                    POOH.append(df1.iloc[i].tolist())
                    index2 += 1
                else:
                    j1 = 0
            elif i == len(df1) - 1:
                if df1[col1].iloc[i] > df1[col1].iloc[i - 1]:
                    RIH.append(df1.iloc[i].tolist())
                elif df1[col1].iloc[i] < df1[col1].iloc[i - 1]:
                    POOH.append(df1.iloc[i].tolist())
                else:
                    j2 = i
                    if df1[col1].iloc[j1 - 1] > df1[col1].iloc[j1]:
                        POOH.append([])
                        for col in df1.columns:
                            if repr == 'mean':
                                POOH[index2].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'min':
                                POOH[index2].append(min(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'max':
                                POOH[index2].append(max(df1[col].iloc[j1:j2 + 1]))
                    else:
                        RIH.append([])
                        for col in df1.columns:
                            if repr == 'mean':
                                RIH[index1].append(statistics.mean(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'min':
                                RIH[index1].append(min(df1[col].iloc[j1:j2 + 1]))
                            elif repr == 'max':
                                RIH[index1].append(max(df1[col].iloc[j1:j2 + 1]))

        RIH = RIH[:RIH.index(max(RIH)) + 1]
        POOH = POOH[POOH.index(max(POOH)):]
        return RIH, POOH

    def operationDefine(self, index1, index2, df2):
        # determine RIH/POOH operation
        operation = 'No data'
        if index1 is not None and index2 is not None:
            RIH, POOH = self.splitlogs(df2, 'mean')
            if RIH != [] and POOH != []:
                operation = 'RIH, POOH'
            elif RIH:
                operation = 'RIH'
            elif POOH:
                operation = 'POOH'
        elif index1 is not None:
            operation = 'No data'
        elif index2 is not None:
            RIH, POOH = self.splitlogs(df2, 'mean')
            if RIH != [] and POOH != []:
                operation = 'RIH, POOH'
            elif RIH:
                operation = 'RIH'
            elif POOH:
                operation = 'POOH'
        else:
            operation = 'Not defined'
        return operation

    def csvcolumns(self, df0, x, y, c):
        df01 = self.csvpreprocess(df0)
        # update csv depending on column header location
        if x != '':
            x = int(x)
            columns = []
            for col in df01.columns:
                if y != '':
                    columns.append(str(df01[col].iloc[x]) + ', ' + str(df01[col].iloc[y]))
                else:
                    columns.append(str(df01[col].iloc[x]))
            df01.columns = columns
            df2 = pd.DataFrame(data=df01.iloc[c:].values, columns=df01.columns)
        else:
            columns = []
            for col in df01.columns:
                if y != '':
                    columns.append(str(col) + ', ' + str(df01[col].iloc[y]))
                else:
                    columns.append(str(col))
            df01.columns = columns
            df2 = pd.DataFrame(data=df01.iloc[c:].values, columns=df01.columns)

        return df2

    def csvnumeric(self, df1):
        for col in df1.columns:
            if str(col).lower().find('time') == -1:
                df1[col] = df1[col].astype('str')
                df1[col] = df1[col].astype('float')
        return df1

    def summary_dataframe(self, object, **kwargs):
        df = pd.DataFrame()
        for i, (key, value) in enumerate(kwargs.items()):
            list_of_values = []
            for item in object:
                try:
                    x = getattr(item, key)
                    list_of_values.append(x)
                except:
                    list_of_values.append('')
                    continue
            df[value] = list_of_values
        return df.sort_values(df.columns[0])

    pass


class Visualization:
    """Functions to visualize data"""

    def generate_axis_title(self, mnemonic, descr, unit):
        if descr != '':
            title_words = descr.split(" ")
            current_line = ""
            lines = []
            for word in title_words:
                if len(current_line) + len(word) > 15:
                    lines.append(current_line[:-1])
                    current_line = ""
                current_line += "{} ".format(word)
            lines.append(current_line)

            title = "<br>".join(lines)
            if title[1] == " ":
                title = title[2:]
            elif title[2] == " ":
                title = title[3:]
            title += "<br>({})".format(unit)
        else:
            title = mnemonic
        return title

    def generate_curvesTime(self, lf, mnem):
        # Visualize LAS from Time
        plots = []
        for i in range(len(lf.curves)):
            if str(lf.curves[i]['mnemonic']).lower().find(r'tim') == -1:
                plots.append([lf.curves[i]["mnemonic"]])

        xvals = mnem
        xvalsvalues = []
        for k in range(len(lf.curves[xvals].data)):
            if str(lf.curves[xvals].data[k]).find(r'NaN') == -1:
                xvalsvalues.append(float(lf.curves[xvals].data[k]))

        fig = subplots.make_subplots(
            rows=len(plots), cols=1, shared_xaxes=True, horizontal_spacing=0.01, vertical_spacing=0.01, print_grid=True
        )

        for i in range(len(plots)):
            list_of_floats = []
            for k in range(len(lf.curves[plots[i][0]].data)):
                if str(lf.curves[plots[i][0]].data[k]).find(r'NaN') == -1 and str(lf.curves[plots[i][0]].data[k]).find(
                        r'-999.25') == -1:
                    list_of_floats.append(float(lf.curves[plots[i][0]].data[k]))
            fig.append_trace(
                go.Scatter(
                    x=xvalsvalues,
                    y=list_of_floats,
                    name=lf.curves[plots[i][0]]["mnemonic"],
                    line={"dash": "solid", },
                ),
                row=i + 1,
                col=1,
            )
            fig["layout"]["yaxis{}".format(i + 1)].update(
                title_text=self.generate_axis_title(lf.curves[plots[i][0]]["mnemonic"], lf.curves[plots[i][0]]["descr"],
                                                    lf.curves[plots[i][0]]["unit"]))
            if i == len(plots) - 1:
                fig.update_xaxes(
                    title_text=self.generate_axis_title(lf.curves[xvals]["mnemonic"], lf.curves[xvals]["descr"],
                                                        lf.curves[xvals]["unit"]), row=i + 1, col=1)

        fig["layout"].update(
            height=200 * len(plots),
            width=1600,
            font=dict(
                size=10),
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode="y",
            margin=go.layout.Margin(r=100, t=100, b=50, l=80, autoexpand=True),
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON

    def generate_curves(self, lf, mnem):
        # visualize LAS from Depth
        plots = []
        for i in range(len(lf.curves)):
            if str(lf.curves[i]['mnemonic']).find(r'TIM') == -1 and str(lf.curves[i]['mnemonic']).find(r'DEP') == -1:
                plots.append([lf.curves[i]["mnemonic"]])

        yvals = mnem
        yvalsvalues = []
        for k in range(len(lf.curves[yvals].data)):
            if str(lf.curves[yvals].data[k]).find(r'NaN') == -1:
                yvalsvalues.append(float(lf.curves[yvals].data[k]))
        rows1 = round(len(plots) / 8) + 1

        if len(plots) < 8:
            cols1 = len(plots)
        else:
            cols1 = 8

        fig = subplots.make_subplots(
            rows=rows1, cols=cols1, shared_yaxes=True, horizontal_spacing=0.01, vertical_spacing=0.05, print_grid=True
        )

        t = 0

        for i in range(rows1):
            for j in range(cols1):
                if t < len(plots):
                    list_of_floats = []
                    for k in range(len(lf.curves[plots[t][0]].data)):
                        if str(lf.curves[plots[t][0]].data[k]).find(r'NaN') == -1 and str(
                                lf.curves[plots[t][0]].data[k]).find(r'-999.25') == -1:
                            list_of_floats.append(float(lf.curves[plots[t][0]].data[k]))
                    fig.append_trace(
                        go.Scatter(
                            x=list_of_floats,
                            y=yvalsvalues,
                            name=lf.curves[plots[t][0]]["mnemonic"],
                            line={"dash": "solid", },
                        ),
                        row=i + 1,
                        col=j + 1,
                    )
                    fig["layout"]["xaxis{}".format(t + 1)].update(
                        title=go.layout.xaxis.Title(text=self.generate_axis_title(lf.curves[plots[t][0]]["mnemonic"],
                                                                                  lf.curves[plots[t][0]]["descr"],
                                                                                  lf.curves[plots[t][0]]["unit"]),
                                                    ), side="top",
                        type="log" if lf.curves[plots[t][0]]["mnemonic"] in plots[1] else "linear",
                        mirror=True,
                    )

                    fig.update_yaxes(
                        title_text=self.generate_axis_title(lf.curves[yvals]["mnemonic"], lf.curves[yvals]["descr"],
                                                            lf.curves[yvals]["unit"]), autorange="reversed", row=i + 1,
                        col=1)
                    t += 1

            fig["layout"].update(
                height=1000 * rows1,
                width=1600,
                font=dict(
                    size=10),
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode="y",
                margin=go.layout.Margin(r=100, t=100, b=50, l=80, autoexpand=True),
            )

            fig.update_yaxes(showline=True, linewidth=0.2, spikedash='dash', linecolor='black', mirror=False)

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON

    def generate_curvesCSV(self, df):
        # visualize CSV data from Time
        for col in df.columns:
            if str(col).lower().find(r'tim') != -1:
                col1 = col
                pass
        random_x = df[col1].values
        y = []
        y1 = []
        for col in df.columns:
            if str(col).find(r'Time') == -1 and str(col).find(r'No.') == -1:
                y.append(pd.to_numeric(df[col].values))
                y1.append(col)

        fig = subplots.make_subplots(
            rows=len(y), cols=1, shared_xaxes=True, vertical_spacing=0.02, print_grid=True
        )

        for i in range(len(y)):
            fig.append_trace(
                go.Scatter(
                    x=random_x,
                    y=y[i],
                    name=y1[i],
                    line={"dash": "solid", }, ),
                row=i + 1, col=1)

        for i in range(len(y)):
            fig.update_yaxes(
                title_text=y1[i], row=i + 1, col=1)

        fig.update_xaxes(title_text='Time', side='top', row=1, col=1, ticks='outside')
        fig.update_xaxes(title_text='Time', side='bottom', row=len(y), col=1, ticks='outside')

        fig["layout"].update(
            height=250 * len(y),
            width=1600,
            font=dict(
                size=10),
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode="y",
            margin=go.layout.Margin(r=100, t=100, b=50, l=80, autoexpand=True),
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return graphJSON

    def generate_curvesDepthCSV(self, dataframe1):
        for col in dataframe1.columns:
            if str(col).lower().find('dept') != -1:
                col1 = col
        random_y = pd.to_numeric(dataframe1[col1].values)
        x = []
        x1 = []
        for col in dataframe1.columns:
            if str(col).lower().find(r'tim') == -1 or str(col).lower().find(r'dept') == -1:
                x.append(pd.to_numeric(dataframe1[col].values))
                x1.append(col)

        fig = subplots.make_subplots(
            rows=1, cols=len(x), shared_yaxes=True, vertical_spacing=0.05, print_grid=True
        )

        for i in range(len(x)):
            fig.append_trace(
                go.Scatter(
                    x=x[i],
                    y=random_y,
                    name=x1[i],
                    line={"dash": "solid", }, ),
                row=1, col=i + 1)

        for i in range(len(x)):
            fig.update_xaxes(
                title_text=x1[i], row=1, col=i + 1)

        fig.update_yaxes(title_text='Depth', autorange='reversed', row=1, col=1)

        fig["layout"].update(
            height=1000,
            width=1600,
            font=dict(
                size=10),
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode="y",
            margin=go.layout.Margin(r=100, t=100, b=50, l=80, autoexpand=False),
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON

    def curvesDepthDLIS(self, frame1):
        curves = frame1.curves()
        channels_names = []

        for i in range(len(frame1.channels)):
            if int(frame1.channels[i].dimension[0]) == 1:
                x = str(frame1.channels[i]).find('(')
                x1 = str(frame1.channels[i]).find(')')
                channels_names.append([str(frame1.channels[i])[x + 1:x1],
                                       str(frame1.channels[i].long_name) + ',' + str(frame1.channels[i].units)])

        yvals = curves[channels_names[0][0]]

        channels_names1 = channels_names[1:]

        rows1 = round(len(channels_names1) / 5) + 1

        cols1 = 5

        fig = subplots.make_subplots(
            rows=rows1, cols=cols1, shared_yaxes=True, horizontal_spacing=0.01, vertical_spacing=0.01, print_grid=True
        )

        t = 0

        for i in range(rows1):
            for j in range(cols1):
                if t < len(channels_names1):
                    fig.append_trace(
                        go.Scatter(
                            x=curves[channels_names1[t][0]],
                            y=yvals,
                            name=channels_names1[t][1],
                            line={"dash": "solid", },
                        ),
                        row=i + 1,
                        col=j + 1,
                    )
                    fig["layout"]["xaxis{}".format(t + 1)].update(
                        title=channels_names1[t][1], side="top",
                        mirror=True,
                    )

                    fig.update_yaxes(
                        title_text=channels_names[0][1], row=i + 1, col=1)
                    t += 1

        fig["layout"].update(
            height=650 * rows1,
            width=1600,
            font=dict(
                size=10),
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode="y",
            margin=go.layout.Margin(r=100, t=100, b=50, l=80, autoexpand=False),
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON

    pass


class CheckFunctions:
    """Functions to check files according to the WD and SiteCom requirements"""

    def unitsrecognized(self, data, type1):
        dataframe1 = Configuration().KDIunits()
        recognized = []
        if type1 == 'las':
            lf = data
            for curve in lf.curves:
                j = 0
                for i in range(len(dataframe1)):
                    if dataframe1['Units'].iloc[i] == curve.unit:
                        recognized.append(dataframe1['Units'].iloc[i])
                        j += 1
                if j == 0:
                    recognized.append('Not found')
            return recognized
        elif type1 == 'csv':
            df2 = data
            mnemoniclist = []
            units = []
            for col in df2.columns:
                mnemoniclist.append(col.split(",")[0])
                units.append(col.split(",")[1].replace(" ", ""))
            k = 0
            for unit in units:
                j = 0
                for i in range(len(dataframe1)):
                    if dataframe1['Units'].iloc[i] == unit:
                        print(dataframe1['Units'].iloc[i], unit)
                        recognized.append(dataframe1['Units'].iloc[i])
                        j += 1
                if j == 0:
                    recognized.append('')
                    k += 1
            return recognized, mnemoniclist, units
        elif type1 == 'xml':
            Bs_data = BeautifulSoup(data, "xml")
            line1 = Bs_data.find_all('mnemonicList')
            line2 = Bs_data.find_all('unitList')
            line0 = []
            for row in line1:
                line0.append(row.get_text())
            line01 = []
            for row in line2:
                line01.append(row.get_text())

            line = str(line0[0])
            mnemoniclist = line.split(',')

            line = str(line01[0])
            units = line.split(',')

            k = 0
            for unit in units:
                j = 0
                for i in range(len(dataframe1)):
                    if dataframe1['Units'].iloc[i] == unit:
                        recognized.append(dataframe1['Units'].iloc[i])
                        j += 1
                if j == 0:
                    recognized.append('')
                    k += 1
            return recognized, mnemoniclist, units

    def checklasfunction(self, lf):
        if lf.curves[0].descr.lower().find('dept') != -1:
            indexType = 'measured depth'
        elif lf.curves[0].descr.lower().find('time') != -1:
            indexType = 'date time'

        structure = []
        # check_structure
        st, st1 = Configuration().serviceTypeOptions()
        WD_equipmentType = dict(st)
        WD_equipmentType_list = list(WD_equipmentType.values())
        st, st1 = Configuration().dataTypeOptions()
        WD_dataType = dict(st)
        WD_dataType_list = list(WD_dataType.values())

        file = open('configuration/lognames.txt')
        lognames = [line.rstrip('\n') for line in file]

        if indexType == 'date time':
            for curve in lf.curves:
                if re.search(r'^[A-Z]+_[A-Z]+_[A-Z]+$', curve.mnemonic) is not None:
                    structure.append('Yes')
                else:
                    structure.append('No')
        else:
            for curve in lf.curves:
                if re.search(r'^[A-Z]+_[A-Z]+_[0-9]+_[A-Z]+$', curve.mnemonic) is not None:
                    structure.append('Yes')
                else:
                    structure.append('No')

        equipmenttype = []
        datatype = []
        runnumbers = []
        lognamesrec = []
        for i in range(len(lf.curves)):
            if structure[i] == 'Yes':
                s1 = lf.curves[i].mnemonic.split('_')
                k = 0
                for mnem in WD_equipmentType_list:
                    if s1[0] == mnem:
                        k += 1
                        equipmenttype.append(mnem)
                if k == 0:
                    equipmenttype.append('Not found')
                k = 0
                for item in WD_dataType_list:
                    if s1[1] == item:
                        datatype.append(item)
                        k += 1
                if k == 0:
                    datatype.append('Not found')

                if indexType == 'date time':
                    k = 0
                    for item in lognames:
                        if s1[2] == item:
                            lognamesrec.append(item)
                            k += 1
                    if k == 0:
                        lognamesrec.append('Not found')
                else:
                    k = 0
                    if re.search('[0-9]', s1[2]) is not None:
                        runnumbers.append(s1[2])
                        k += 1
                    if k == 0:
                        runnumbers.append('Not found')
                    k = 0
                    for item in lognames:
                        if s1[3] == item:
                            lognamesrec.append(item)
                            k += 1
                    if k == 0:
                        lognamesrec.append('Not found')
            else:
                equipmenttype.append('Not found')
                datatype.append('Not found')
                runnumbers.append('Not found')
                lognamesrec.append('Not found')

        return structure, equipmenttype, datatype, runnumbers, lognamesrec

    def lastimestamp(self, lf):
        if lf.curves[0].descr.lower().find('time') != -1:
            string1 = str(lf.curves[0].data[0])
            check = re.search(
                '^[0-9]{4}(-)[0-9]{2}(-)[0-9]{2}(T)[0-9]{2}(:)[0-9]{2}(:)[0-9]{2}(.)[0-9]{3}.[0-9]{2}(:)[0-9]{2}$',
                string1)
            check1 = re.search('^[0-9]{4}(-)[0-9]{2}(-)[0-9]{2}(T)[0-9]{2}(:)[0-9]{2}(:)[0-9]{2}(.)[0-9]{3}Z$', string1)
            if check is not None or check1 is not None:
                result = 'Correct'
            else:
                result = 'Incorrect'
        else:
            result = 'No timestamp - Depth Index'
        return result

    def lasWDtags(self, lf):
        description = ''
        serviceCategory = ''
        dataSource = ''

        for item in lf.well:
            if str(item).find('description') != -1:
                description += 'Yes'
            if str(item).find('serviceCategory') != -1:
                serviceCategory += 'Yes'
            if str(item).find('dataSource') != -1:
                dataSource += 'Yes'
        for item in lf.other:
            if str(item).find('description') != -1:
                description += 'Yes'
            if str(item).find('serviceCategory') != -1:
                serviceCategory += 'Yes'
            if str(item).find('dataSource') != -1:
                dataSource += 'Yes'
        for item in lf.params:
            if str(item).find('description') != -1:
                description += 'Yes'
            if str(item).find('serviceCategory') != -1:
                serviceCategory += 'Yes'
            if str(item).find('dataSource') != -1:
                dataSource += 'Yes'

        if description == '':
            description = 'No data'
        if serviceCategory == '':
            serviceCategory = 'No data'
        if dataSource == '':
            dataSource = 'No data'
        return description, serviceCategory, dataSource

    def checkcsvfunction(self, indexType, mnemoniclist):
        structure = []
        # check_structure

        st, st1 = Configuration().serviceTypeOptions()
        WD_equipmentType = dict(st)
        WD_equipmentType_list = list(WD_equipmentType.values())
        st, st1 = Configuration().dataTypeOptions()
        WD_dataType = dict(st)
        WD_dataType_list = list(WD_dataType.values())

        file = open('configuration/lognames.txt')
        lognames = [line.rstrip('\n') for line in file]

        if indexType == 'date time':
            for mnem in mnemoniclist:
                if re.search(r'^[A-Z]+_[A-Z]+_[A-Z]+$', str(mnem)) is not None:
                    structure.append('Yes')
                else:
                    structure.append('No')
        else:
            for mnem in mnemoniclist:
                if re.search(r'^[A-Z]+_[A-Z]+_[0-9]+_[A-Z]+$', str(mnem)) is not None:
                    structure.append('Yes')
                else:
                    structure.append('No')

        equipmenttype = []
        datatype = []
        runnumbers = []
        lognamesrec = []
        for i in range(len(mnemoniclist)):
            if structure[i] == 'Yes':
                s1 = mnemoniclist[i].split('_')
                k = 0
                for mnem in WD_equipmentType_list:
                    if s1[0] == mnem:
                        k += 1
                        equipmenttype.append(mnem)
                if k == 0:
                    equipmenttype.append('Not found')
                k = 0
                for item in WD_dataType_list:
                    if s1[1] == item:
                        datatype.append(item)
                        k += 1
                if k == 0:
                    datatype.append('Not found')

                if indexType == 'date time':
                    k = 0
                    for item in lognames:
                        if s1[2] == item:
                            lognamesrec.append(item)
                            k += 1
                    if k == 0:
                        lognamesrec.append('Not found')
                else:
                    k = 0
                    if re.search('[0-9]', s1[2]) is not None:
                        runnumbers.append(s1[2])
                        k += 1
                    if k == 0:
                        runnumbers.append('Not found')
                    k = 0
                    for item in lognames:
                        if s1[3] == item:
                            lognamesrec.append(item)
                            k += 1
                    if k == 0:
                        lognamesrec.append('Not found')
            else:
                equipmenttype.append('Not found')
                datatype.append('Not found')
                runnumbers.append('Not found')
                lognamesrec.append('Not found')

        return structure, equipmenttype, datatype, runnumbers, lognamesrec

    def csvtimestamp(self, df2):
        k = 0
        for col in df2.columns:
            if col.lower().find(r'tim') != -1:
                string1 = str(df2[col].iloc[0])
                check = re.search(
                    '^[0-9]{4}(-)[0-9]{2}(-)[0-9]{2}(T)[0-9]{2}(:)[0-9]{2}(:)[0-9]{2}(.)[0-9]{3}.[0-9]{2}(:)[0-9]{2}$',
                    string1)
                check1 = re.search('^[0-9]{4}(-)[0-9]{2}(-)[0-9]{2}(T)[0-9]{2}(:)[0-9]{2}(:)[0-9]{2}(.)[0-9]{3}Z$',
                                   string1)
                if check is not None or check1 is not None:
                    result = 'Correct'
                else:
                    result = 'Incorrect'
                k += 1
        if k == 0:
            result = 'No timestamp - Depth Index'
        return result

    def csvWDtags(self, df2):
        description = ''
        serviceCategory = ''
        dataSource = ''

        x = df2.to_string()

        if x.find('description') != -1:
            description += 'Yes'
        if x.find('serviceCategory') != -1:
            serviceCategory += 'Yes'
        if x.find('dataSource') != -1:
            dataSource += 'Yes'

        if description == '':
            description = 'No data'
        if serviceCategory == '':
            serviceCategory = 'No data'
        if dataSource == '':
            dataSource = 'No data'
        return description, serviceCategory, dataSource

    def xmlWDtags(self, data1):
        description = 'No data'
        serviceCategory = 'No data'
        dataSource = 'No data'
        Bs_data = BeautifulSoup(data1, "xml")
        line1 = Bs_data.find_all('description')
        line2 = Bs_data.find_all('serviceCategory')
        line3 = Bs_data.find_all('dataSource')
        if len(line1) != 0:
            description = 'Yes'
        if len(line2) != 0:
            serviceCategory = 'Yes'
        if len(line3) != 0:
            dataSource = 'Yes'
        line0 = []
        for row in line2:
            line0.append(row.get_text())
        line00 = line0[0].split(',')
        if len(line00) == 4:
            servicetype, choices = Configuration().serviceTypeOptions()
            strreg = ''
            for service in servicetype:
                if line00[2] == service[1]:
                    strreg = 'Yes'
            datatype, choices = Configuration().dataTypeOptions()
            strreg1 = ''
            for datat in datatype:
                if line00[3] == datat[1]:
                    strreg1 = 'Yes'
            if strreg == 'Yes' and strreg1 == 'Yes':
                result = 'Recognized'
            else:
                result = 'Not found'
        else:
            result = 'No tag'
        return description, serviceCategory, dataSource, result

    def xmlKDItags(self, data1):
        Bs_data = BeautifulSoup(data1, "xml")
        line1 = Bs_data.find_all('indexType')
        index = []
        for row in line1:
            index.append(row.get_text())
        if index[0] == 'date time':
            mandatory = ['name', 'indexType', 'minDateTimeIndex', 'maxDateTimeIndex', 'typeLogData', 'mnemonicList',
                         'unitList']
        else:
            mandatory = ['name', 'indexType', 'minIndex', 'maxIndex', 'typeLogData', 'mnemonicList', 'unitList']
        missing = []
        for each in mandatory:
            line = Bs_data.find_all(each)
            if len(line) == 0:
                missing.append(each)
        if len(missing) != 0:
            missing_string = 'Missing tags: ' + ','.join(missing)
        else:
            missing_string = 'No missing tags'
        line1 = Bs_data.find_all('mnemonicList')
        line2 = Bs_data.find_all('unitList')
        line0 = []
        for row in line1:
            line0.append(row.get_text())
        line01 = []
        for row in line2:
            line01.append(row.get_text())
        line = str(line0[0])
        mnem = line.split(',')
        line = str(line01[0])
        units = line.split(',')
        if len(mnem) != len(units):
            missing_string += '\n Mnemonics do not correspond to units'
        return missing_string

    def checkdlisfunction(self, indexType, mnemoniclist):
        structure = []
        # check_structure

        st, st1 = Configuration().serviceTypeOptions()
        WD_equipmentType = dict(st)
        WD_equipmentType_list = list(WD_equipmentType.values())
        st, st1 = Configuration().dataTypeOptions()
        WD_dataType = dict(st)
        WD_dataType_list = list(WD_dataType.values())

        file = open('configuration/lognames.txt')
        lognames = [line.rstrip('\n') for line in file]

        if indexType == 'date time':
            for mnem in mnemoniclist:
                if re.search(r'^[A-Z]+_[A-Z]+_[A-Z]+$', str(mnem)) is not None:
                    structure.append('Yes')
                else:
                    structure.append('No')
        else:
            for mnem in mnemoniclist:
                if re.search(r'^[A-Z]+_[A-Z]+_[0-9]+_[A-Z]+$', str(mnem)) is not None:
                    structure.append('Yes')
                else:
                    structure.append('No')

        equipmenttype = []
        datatype = []
        runnumbers = []
        lognamesrec = []
        for i in range(len(mnemoniclist)):
            if structure[i] == 'Yes':
                s1 = mnemoniclist[i].split('_')
                k = 0
                for mnem in WD_equipmentType_list:
                    if s1[0] == mnem:
                        k += 1
                        equipmenttype.append(mnem)
                if k == 0:
                    equipmenttype.append('Not found')
                k = 0
                for item in WD_dataType_list:
                    if s1[1] == item:
                        datatype.append(item)
                        k += 1
                if k == 0:
                    datatype.append('Not found')

                if indexType == 'date time':
                    k = 0
                    for item in lognames:
                        if s1[2] == item:
                            lognamesrec.append(item)
                            k += 1
                    if k == 0:
                        lognamesrec.append('Not found')
                else:
                    k = 0
                    if re.search('[0-9]', s1[2]) is not None:
                        runnumbers.append(s1[2])
                        k += 1
                    if k == 0:
                        runnumbers.append('Not found')
                    k = 0
                    for item in lognames:
                        if s1[3] == item:
                            lognamesrec.append(item)
                            k += 1
                    if k == 0:
                        lognamesrec.append('Not found')
            else:
                equipmenttype.append('Not found')
                datatype.append('Not found')
                runnumbers.append('Not found')
                lognamesrec.append('Not found')

        return structure, equipmenttype, datatype, runnumbers, lognamesrec

    def dlistimestamp(self, f):
        for frame in f.frames:
            if str(frame.index_type).lower().find('tim') != -1:
                check = re.search(
                    '^[0-9]{4}(-)[0-9]{2}(-)[0-9]{2}(T)[0-9]{2}(:)[0-9]{2}(:)[0-9]{2}(.)[0-9]{3}.[0-9]{2}(:)[0-9]{2}$',
                    frame.index_type)
                check1 = re.search('^[0-9]{4}(-)[0-9]{2}(-)[0-9]{2}(T)[0-9]{2}(:)[0-9]{2}(:)[0-9]{2}(.)[0-9]{3}Z$',
                                   frame.index_type)
                if check is not None or check1 is not None:
                    result = 'Correct'
                else:
                    result = 'Incorrect'
            else:
                result = 'No timestamp - Depth Index'
        return result

    def dlisWDtags(self, f):
        description = ''
        serviceCategory = ''
        dataSource = ''

        if len(f.find('description')) > 0:
            description += 'Yes'
        if len(f.find('serviceCategory')) > 0:
            serviceCategory += 'Yes'
        if len(f.find('dataSource')) > 0:
            dataSource += 'Yes'

        if description == '':
            description = 'No data'
        if serviceCategory == '':
            serviceCategory = 'No data'
        if dataSource == '':
            dataSource = 'No data'
        return description, serviceCategory, dataSource

    def errorLog(self, generalInfo, fileInfo, df, summary):
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
        with open('errorlog/' + str(dt_string) + 'errorlog.txt', 'w') as f:
            f.write('Date: ' + str(date.today()))
            f.write('\n\n\nFile Information:' + '\n')
            f.write(tabulate(fileInfo, headers='keys', tablefmt='rst', showindex=False))
            f.write('\n\n\nGeneral Information:' + '\n')
            f.write(tabulate(generalInfo, headers='keys', tablefmt='rst', showindex=False))
            f.write('\n\n\nTimestamp and WD tag information check:' + '\n')
            f.write(tabulate(df, headers='keys', tablefmt='rst', showindex=False))  #
            f.write('\n\n\nMnemonic and Units Recognition:' + '\n')
            f.write(tabulate(summary, headers='keys', tablefmt='rst', showindex=False))

    pass


class XmlGeneration:
    """Functions to generate XML"""

    # pretty-printed XML
    def prettify(self, elem):
        rough_string = tostring(elem, encoding='utf-8', method='xml')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def lastoxml(self, lf, filename, uidWell, uidWellbore, BU, asset, purpose1, servicecompany, wellname1, idwi, runid,
                 servicetype,
                 datatype, uid,
                 creationDate,
                 wellbore_name,
                 direction,
                 datasource,
                 nullValue,
                 indexType,
                 startDateTimeIndex,
                 endDateTimeIndex,
                 indexCurve,
                 startIndex,
                 endIndex,
                 dataSize):

        mandatory_time = ['name', 'indexType', 'minDateTimeIndex', 'maxDateTimeIndex', 'typeLogData', 'mnemonicList',
                          'unitList']
        mandatory_depth = ['name', 'indexType', 'minIndex', 'maxIndex', 'typeLogData', 'mnemonicList', 'unitList']

        name = filename
        wellname = wellname1
        wellbore = wellbore_name
        SC = servicecompany
        runNumber = runid
        creationDate = creationDate
        indexType = indexType
        startDateTimeIndex = startDateTimeIndex
        endDateTimeIndex = endDateTimeIndex
        indexCurve = indexCurve
        nullValue = nullValue
        startIndex = startIndex
        endIndex = endIndex
        direction = direction
        datasource = datasource
        if dataSize < 10000:
            maxDataNodes = dataSize
            filesplit = False
        else:
            maxDataNodes = 10000
            filesplit = True

        comments = 'BU: ' + str(BU) + '\nAsset:' + str(asset)
        servicecategory = str(idwi) + ',' + str(runid) + ',' + str(servicetype) + ',' + str(datatype)
        description = str(purpose1)

        mnemoniclist = []
        units = []
        for curve in lf.curves:
            mnemoniclist.append(curve['mnemonic'])
            if str(curve['unit']) != '':
                units.append(curve['unit'])
            else:
                units.append('unitless')


        unitstring = ','.join(units)
        mnemonicstring = ','.join(mnemoniclist)

        splitcount_bottom = 0
        splitcount_top = maxDataNodes
        file_counter = 1
        while lf.data.shape[0] >= splitcount_top:
            # print(lf.data.shape[0] >= splitcount_top)
            top = Element('logs', xmlns="http://www.witsml.org/schemas/1series", version="1.4.1.1")
            top_1 = SubElement(top, 'log', uidWell=uidWell, uidWellbore=uidWellbore, uid=uid)
            top_1_1 = SubElement(top_1, 'nameWell')
            top_1_1.text = str(wellname)
            top_1_2 = SubElement(top_1, 'nameWellbore')
            top_1_2.text = str(wellbore_name)
            top_1_3 = SubElement(top_1, 'name')
            top_1_3.text = str(name)
            top_1_4 = SubElement(top_1, 'serviceCompany')
            top_1_4.text = str(SC)
            top_1_5 = SubElement(top_1, 'runNumber')
            top_1_5.text = str(runNumber)
            top_1_6 = SubElement(top_1, 'creationDate')
            top_1_6.text = str(creationDate)
            top_1_7 = SubElement(top_1, 'description')
            top_1_7.text = str(description)
            top_1_8 = SubElement(top_1, 'indexType')
            top_1_8.text = str(indexType)
            if indexType == 'date time':
                top_1_9 = SubElement(top_1, 'startDateTimeIndex')
                top_1_9.text = str(startDateTimeIndex)
                top_1_10 = SubElement(top_1, 'endDateTimeIndex')
                top_1_10.text = str(endDateTimeIndex)
            else:
                top_1_9a = SubElement(top_1, 'startIndex', uom='m')
                top_1_9a.text = str(startIndex)
                top_1_10a = SubElement(top_1, 'endIndex', uom='m')
                top_1_10a.text = str(endIndex)
            top_1_10b = SubElement(top_1, 'direction')
            top_1_10b.text = str(direction)
            top_1_11 = SubElement(top_1, 'indexCurve')
            top_1_11.text = str(indexCurve)
            top_1_12 = SubElement(top_1, 'nullValue')
            top_1_12.text = str(nullValue)
            j = 1
            for curve in lf.curves:
                top_2 = SubElement(top_1, 'logCurveInfo', uid=curve.mnemonic)
                child1 = SubElement(top_2, 'mnemonic')
                child1.text = str(curve.mnemonic)
                child1a = SubElement(top_2, 'unit')
                child1a.text = str(units[j - 1])
                if indexType == 'date time':
                    child2 = SubElement(top_2, 'minDateTimeIndex')
                    child2.text = str(startDateTimeIndex)
                    child3 = SubElement(top_2, 'maxDateTimeIndex')
                    child3.text = str(endDateTimeIndex)
                else:
                    child2 = SubElement(top_2, 'minIndex', uom='m')
                    child2.text = str(startIndex)
                    child3 = SubElement(top_2, 'maxIndex', uom='m')
                    child3.text = str(endIndex)
                child4 = SubElement(top_2, 'curveDescription')
                child4.text = str(re.sub(' +', ' ', curve.descr))
                child4a = SubElement(top_2, 'dataSource')
                child4a.text = str(datasource)
                child5 = SubElement(top_2, 'typeLogData')
                if curve['mnemonic'].lower().find('time') != -1:
                    child5.text = 'date time'
                else:
                    child5.text = 'double'
                j += 1
            top_3 = SubElement(top_1, 'logData')
            top_3_1 = SubElement(top_3, 'mnemonicList')
            top_3_1.text = str(mnemonicstring)
            top_3_2 = SubElement(top_3, 'unitList')
            top_3_2.text = str(unitstring)
            # for i in range(len(lf.data)):
            for i in range(splitcount_bottom, splitcount_top):
                top_3_3 = SubElement(top_3, 'data')
                text = ','.join(str(v) for v in lf.data[i])
                # if text.find('NaN') != -1:
                # text = text.replace('NaN', '-0.0')
                top_3_3.text = text
                # print(i)
                # print(text)
            top_4 = SubElement(top_1, 'commonData')
            top_4_1 = SubElement(top_4, 'dTimCreation')
            date1 = str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])
            date1 += '+00:00'
            top_4_1.text = date1
            # serviceCategory should come before comments
            top_4_3 = SubElement(top_4, 'serviceCategory')
            top_4_3.text = servicecategory
            top_4_2 = SubElement(top_4, 'comments')
            top_4_2.text = comments

            stringfile = self.prettify(top)

            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
            if filesplit:
                naming_string = filename + '_part_{}'.format(file_counter)
            else:
                naming_string = filename
            desktop = os.path.expanduser("generatedXML/" + str(naming_string) + '.xml')
            with open(desktop, "w") as f:
                f.write(stringfile)
            file_counter += 1
            splitcount_bottom += maxDataNodes
            data_dif = lf.data.shape[0] - splitcount_top
            if data_dif < maxDataNodes and data_dif != 0:
                splitcount_top = splitcount_top + data_dif
            else:
                splitcount_top += maxDataNodes
            # print(lf.data.shape[0])
            # print(splitcount_top)

        # tree = ElementTree(top)
        # tree.write(os.path.expanduser("~/Desktop/filename1.xml"))

        missingData = []
        lst = top.findall('log/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('commonData/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('logCurveInfo/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('logData/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        missingMandatory = []
        missingOptional = []

        for each in missingData:
            j = 0
            if indexType == 'date time':
                for each1 in mandatory_time:
                    if each == each1:
                        missingMandatory.append(each)
                        j += 1
            else:
                for each1 in mandatory_depth:
                    if each == each1:
                        missingMandatory.append(each)
                        j += 1
            if j == 0:
                missingOptional.append(each)

        missingOptional1 = set(missingOptional)
        missingMandatory1 = set(missingMandatory)

        if len(missingMandatory1) != 0:
            missingMandatoryString = ', '.join(missingMandatory1)
        else:
            missingMandatoryString = 'None'
        if len(missingOptional1) != 0:
            missingOptionalString = ', '.join(missingOptional1)
        else:
            missingOptionalString = 'None'

        if len(mnemoniclist) == len(units):
            missing3 = 'Yes'
        else:
            missing3 = 'None'

        return stringfile, missingMandatoryString, missingOptionalString, missing3

    # def lascheck(self, lf):

    def csvtoxml(self, df, df2, x, c, filename, uidWell, uidWellbore, BU, asset, purpose1, servicecompany, wellname1,
                 idwi,
                 runid,
                 servicetype, datatype, uid,
                 creationDate,
                 wellbore_name,
                 direction,
                 datasource,
                 nullValue,
                 indexType,
                 startDateTimeIndex,
                 endDateTimeIndex,
                 indexCurve,
                 startIndex,
                 endIndex,
                 dataSize):

        mandatory_time = ['name', 'indexType', 'minDateTimeIndex', 'maxDateTimeIndex', 'typeLogData', 'mnemonicList',
                          'unitList']
        mandatory_depth = ['name', 'indexType', 'minIndex', 'maxIndex', 'typeLogData', 'mnemonicList', 'unitList']

        name = filename
        wellname = wellname1
        wellbore = wellbore_name
        SC = servicecompany
        runNumber = runid
        creationDate = creationDate
        indexType = indexType
        startDateTimeIndex = startDateTimeIndex
        endDateTimeIndex = endDateTimeIndex
        indexCurve = indexCurve
        nullValue = nullValue
        startIndex = startIndex
        endIndex = endIndex
        direction = direction
        datasource = datasource

        if dataSize < 10000:
            maxDataNodes = dataSize
            filesplit = False
        else:
            maxDataNodes = 10000
            filesplit = True

        comments = 'BU: ' + str(BU) + '\nAsset:' + str(asset)
        servicecategory = str(idwi) + ',' + str(runid) + ',' + str(servicetype) + ',' + str(datatype)
        description = str(purpose1)

        mnemoniclist = []
        units = []
        for col in df2.columns:
            mnemoniclist.append(col.split(",")[0])
            units.append(col.split(",")[1].replace(" ", ""))

        for unit in units:
            if unit == ' ':
                unit = 'unitless'
        unitstring = ','.join(str(v) for v in units)
        unitstring = unitstring.replace(" ", "")
        mnemonicstring = ','.join(str(v) for v in mnemoniclist)

        splitcount_bottom = c
        splitcount_top = maxDataNodes
        file_counter = 1
        p = 0
        while df2.shape[0] >= splitcount_top:

            top = Element('logs', xmlns="http://www.witsml.org/schemas/1series", version="1.4.1.1")
            top_1 = SubElement(top, 'log', uidWell=uidWell, uidWellbore=uidWellbore, uid=uid)
            top_1_1 = SubElement(top_1, 'nameWell')
            top_1_1.text = wellname
            top_1_2 = SubElement(top_1, 'nameWellbore')
            top_1_2.text = str(wellbore)
            top_1_3 = SubElement(top_1, 'name')
            top_1_3.text = name
            top_1_4 = SubElement(top_1, 'serviceCompany')
            top_1_4.text = SC
            top_1_5 = SubElement(top_1, 'runNumber')
            top_1_5.text = str(runNumber)
            top_1_6 = SubElement(top_1, 'creationDate')
            top_1_6.text = str(creationDate)
            top_1_7 = SubElement(top_1, 'description')
            top_1_7.text = description
            top_1_8 = SubElement(top_1, 'indexType')
            top_1_8.text = indexType
            if indexType == 'date time':
                top_1_9 = SubElement(top_1, 'startDateTimeIndex')
                top_1_9.text = str(startDateTimeIndex)
                top_1_10 = SubElement(top_1, 'endDateTimeIndex')
                top_1_10.text = str(endDateTimeIndex)
            else:
                top_1_9a = SubElement(top_1, 'startIndex', uom='m')
                top_1_9a.text = str(startIndex)
                top_1_10a = SubElement(top_1, 'endIndex', uom='m')
                top_1_10a.text = str(endIndex)
            top_1_10b = SubElement(top_1, 'direction')
            top_1_10b.text = str(direction)
            top_1_11 = SubElement(top_1, 'indexCurve')
            top_1_11.text = indexCurve
            top_1_12 = SubElement(top_1, 'nullValue')
            top_1_12.text = str(nullValue)
            j = 1
            for col in df2.columns:
                top_2 = SubElement(top_1, 'logCurveInfo', uid=str(mnemoniclist[j - 1]))
                child1 = SubElement(top_2, 'mnemonic')
                child1.text = str(mnemoniclist[j - 1])
                child1a = SubElement(top_2, 'unit')
                child1a.text = str(units[j - 1])
                if indexType == 'date time':
                    child2 = SubElement(top_2, 'minDateTimeIndex')
                    child2.text = str(startDateTimeIndex)
                    child3 = SubElement(top_2, 'maxDateTimeIndex')
                    child3.text = str(endDateTimeIndex)
                else:
                    child2 = SubElement(top_2, 'minIndex', uom='m')
                    child2.text = str(startIndex)
                    child3 = SubElement(top_2, 'maxIndex', uom='m')
                    child3.text = str(endIndex)
                child4 = SubElement(top_2, 'curveDescription')
                child4.text = str(mnemoniclist[j - 1])
                child4a = SubElement(top_2, 'dataSource')
                child4a.text = str(datasource)
                child5 = SubElement(top_2, 'typeLogData')
                if col.lower().find('time') != -1:
                    child5.text = 'date time'
                else:
                    child5.text = 'double'
                j += 1
            top_3 = SubElement(top_1, 'logData')
            top_3_1 = SubElement(top_3, 'mnemonicList')
            top_3_1.text = mnemonicstring
            top_3_2 = SubElement(top_3, 'unitList')
            top_3_2.text = unitstring


            for i in range(splitcount_bottom, splitcount_top+c):
                top_3_3 = SubElement(top_3, 'data')
                if x is None or x == '':
                    top_3_3.text = ','.join(str(v) for v in df.iloc[c + p].to_list())
                else:
                    top_3_3.text = ','.join(str(v) for v in df.iloc[c + p].to_list())
                p += 1
                # print(p)
            # print('split')

            top_4 = SubElement(top_1, 'commonData')
            top_4_1 = SubElement(top_4, 'dTimCreation')
            date1 = str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])
            date1 += '+00:00'
            top_4_1.text = date1
            top_4_3 = SubElement(top_4, 'serviceCategory')
            top_4_3.text = servicecategory
            top_4_2 = SubElement(top_4, 'comments')
            top_4_2.text = comments

            stringfile = self.prettify(top)
            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
            if filesplit:
                naming_string = filename + '_part_{}'.format(file_counter)
            else:
                naming_string = filename
            desktop = os.path.expanduser("generatedXML/" + str(naming_string) + '.xml')
            with open(desktop, "w") as f:
                f.write(stringfile)
            file_counter += 1
            splitcount_bottom += maxDataNodes
            data_dif = df2.shape[0] - splitcount_top
            if data_dif < maxDataNodes and data_dif != 0:
                splitcount_top = splitcount_top + data_dif
            else:
                splitcount_top += maxDataNodes
        # tree = ElementTree(top)
        # tree.write(os.path.expanduser("generatedXML/"+ str(date.today()) +'.xml'))

        missingData = []
        lst = top.findall('log/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('commonData/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('logCurveInfo/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('logData/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        # missing = ', '.join(missingData)

        missingMandatory = []
        missingOptional = []

        for each in missingData:
            j = 0
            if indexType == 'date time':
                for each1 in mandatory_time:
                    if each == each1:
                        missingMandatory.append(each)
                        j += 1
            else:
                for each1 in mandatory_depth:
                    if each == each1:
                        missingMandatory.append(each)
                        j += 1
            if j == 0:
                missingOptional.append(each)
        missingOptional1 = set(missingOptional)
        missingMandatory1 = set(missingMandatory)

        if len(missingMandatory1) != 0:
            missingMandatoryString = ', '.join(missingMandatory1)
        else:
            missingMandatoryString = 'None'
        if len(missingOptional1) != 0:
            missingOptionalString = ', '.join(missingOptional1)
        else:
            missingOptionalString = 'None'

        if len(mnemoniclist) == len(units):
            missing3 = 'Yes'
        else:
            missing3 = 'None'

        return stringfile, missingMandatoryString, missingOptionalString, missing3

    def xmltoxml(self, data, uidWell, uidWellbore, BU, asset, purpose1, servicecompany, wellname1,
                 idwi,
                 runid,
                 servicetype, datatype, uid):
        mandatory_time = ['name', 'indexType', 'minDateTimeIndex', 'maxDateTimeIndex', 'typeLogData', 'mnemonicList',
                          'unitList']
        mandatory_depth = ['name', 'indexType', 'minIndex', 'maxIndex', 'typeLogData', 'mnemonicList', 'unitList']
        Bs_data = BeautifulSoup(data, 'xml')
        wellname = wellname1
        description = str(purpose1)
        comments = 'BU: ' + str(BU) + '\nAsset:' + str(asset)
        servicecategory = str(idwi) + ',' + str(runid) + ',' + str(servicetype) + ',' + str(datatype)

        top = Element('logs', xmlns="http://www.witsml.org/schemas/1series", version="1.4.1.1")
        top_1 = SubElement(top, 'log', uidWell=uidWell, uidWellbore=uidWellbore, uid=uid)
        top_1_1 = SubElement(top_1, 'nameWell')
        line1 = Bs_data.find_all(top_1_1.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_1.text = ''.join(index)
        else:
            top_1_1.text = wellname
        top_1_2 = SubElement(top_1, 'nameWellbore')
        line1 = Bs_data.find_all(top_1_2.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_2.text = ''.join(index)
        else:
            top_1_2.text = ''
        top_1_3 = SubElement(top_1, 'name')
        line1 = Bs_data.find_all(top_1_3.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_3.text = ''.join(index)
        else:
            top_1_3.text = ''
        top_1_4 = SubElement(top_1, 'serviceCompany')
        line1 = Bs_data.find_all(top_1_4.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_4.text = ''.join(index)
        else:
            top_1_4.text = servicecompany
        top_1_5 = SubElement(top_1, 'runNumber')
        line1 = Bs_data.find_all(top_1_5.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_5.text = ''.join(index)
        else:
            top_1_5.text = ''
        top_1_6 = SubElement(top_1, 'creationDate')
        line1 = Bs_data.find_all(top_1_6.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_6.text = ''.join(index)
        else:
            top_1_6.text = ''
        top_1_7 = SubElement(top_1, 'description')
        line1 = Bs_data.find_all(top_1_7.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_7.text = ''.join(index)
        else:
            top_1_7.text = description
        top_1_8 = SubElement(top_1, 'indexType')
        line1 = Bs_data.find_all(top_1_8.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_8.text = ''.join(index)
        else:
            top_1_8.text = ''
        if top_1_8.text == 'date time':
            top_1_9 = SubElement(top_1, 'startDateTimeIndex')
            line1 = Bs_data.find_all(top_1_9.tag)
            index = []
            if len(line1) > 0:
                for each in line1:
                    index.append(each.get_text())
                top_1_9.text = ''.join(index)
            else:
                top_1_9.text = ''
            top_1_10 = SubElement(top_1, 'endDateTimeIndex')
            line1 = Bs_data.find_all(top_1_10.tag)
            index = []
            if len(line1) > 0:
                for each in line1:
                    index.append(each.get_text())
                top_1_10.text = ''.join(index)
            else:
                top_1_10.text = ''
        elif top_1_8.text == 'measured depth':
            top_1_9a = SubElement(top_1, 'startIndex')
            line1 = Bs_data.find_all(top_1_9a.tag)
            index = []
            if len(line1) > 0:
                for each in line1:
                    index.append(each.get_text())
                top_1_9a.text = ''.join(index)
            else:
                top_1_9a.text = ''
            top_1_10a = SubElement(top_1, 'endIndex')
            line1 = Bs_data.find_all(top_1_10a.tag)
            index = []
            if len(line1) > 0:
                for each in line1:
                    index.append(each.get_text())
                top_1_10a.text = ''.join(index)
            else:
                top_1_10a.text = ''
        top_1_11 = SubElement(top_1, 'indexCurve')
        line1 = Bs_data.find_all(top_1_11.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_11.text = ''.join(index)
        else:
            top_1_11.text = ''
        top_1_12 = SubElement(top_1, 'nullValue')
        line1 = Bs_data.find_all(top_1_12.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_1_12.text = ''.join(index)
        else:
            top_1_12.text = ''

        line1 = Bs_data.find_all('logCurveInfo')
        line2 = Bs_data.find_all('mnemonic')
        index = []
        if len(line2) > 0:
            for each in line2:
                index.append(each.get_text())
        line3 = Bs_data.find_all('unit')
        index1 = []
        if len(line3) > 0:
            for each in line3:
                index1.append(each.get_text())

        line4 = Bs_data.find_all('curveDescription')
        index2 = []
        if len(line4) > 0:
            for each in line4:
                index2.append(each.get_text())
        line5 = Bs_data.find_all('dataSource')
        index3 = []
        if len(line5) > 0:
            for each in line5:
                index3.append(each.get_text())
        line6 = Bs_data.find_all('typeLogData')
        index4 = []
        if len(line6) > 0:
            for each in line6:
                index4.append(each.get_text())

        for i in range(len(line1)):
            top_2 = SubElement(top_1, 'logCurveInfo', uid=str(i))
            child1 = SubElement(top_2, 'mnemonic')
            if len(line2) > i:
                child1.text = index[i]
            else:
                child1.text = ''
            child1a = SubElement(top_2, 'unit')
            if len(line3) > i:
                child1a.text = index1[i]
            else:
                child1a.text = ''
            child4 = SubElement(top_2, 'curveDescription')
            if len(line4) > i:
                child4.text = index1[i]
            else:
                child4.text = ''
            child4a = SubElement(top_2, 'dataSource')
            if len(line5) > i:
                child4a.text = index1[i]
            else:
                child4a.text = ''
            child5 = SubElement(top_2, 'typeLogData')
            if len(line6) > i:
                child5.text = index1[i]
            else:
                child5.text = ''

        top_3 = SubElement(top_1, 'logData')
        top_3_1 = SubElement(top_3, 'mnemonicList')
        line1 = Bs_data.find_all(top_3_1.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_3_1.text = ''.join(index)
        else:
            top_3_1.text = ''
        top_3_2 = SubElement(top_3, 'unitList')
        line1 = Bs_data.find_all(top_3_2.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_3_2.text = ''.join(index)
        else:
            top_3_2.text = ''

        line4 = Bs_data.find_all('data')
        index = []
        if len(line4) > 0:
            for each in line4:
                index.append(each.get_text())
        for i in range(len(line4)):
            top_3_3 = SubElement(top_3, 'data')
            top_3_3.text = index[i]

        top_4 = SubElement(top_1, 'commonData')
        top_4_1 = SubElement(top_4, 'dTimCreation')
        line1 = Bs_data.find_all(top_4_1.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_4_1.text = ''.join(index)
        else:
            top_4_1.text = str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]) + '+00:00'

        top_4_2 = SubElement(top_4, 'comments')
        line1 = Bs_data.find_all(top_4_2.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_4_2.text = ''.join(index)
        else:
            top_4_2.text = comments

        top_4_3 = SubElement(top_4, 'serviceCategory')
        line1 = Bs_data.find_all(top_4_3.tag)
        index = []
        if len(line1) > 0:
            for each in line1:
                index.append(each.get_text())
            top_4_3.text = ''.join(index)
        else:
            top_4_3.text = servicecategory

        stringfile = self.prettify(top)
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
        desktop = os.path.expanduser("generatedXML/" + str(dt_string) + '.xml')
        with open(desktop, "w") as f:
            f.write(stringfile)
        # tree = ElementTree(top)
        # tree.write(os.path.expanduser("generatedXML/"+ str(date.today()) +'.xml'))

        missingData = []
        lst = top.findall('log/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('commonData/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('logCurveInfo/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('logData/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        # missing = ', '.join(missingData)

        missingMandatory = []
        missingOptional = []

        for each in missingData:
            j = 0
            if top_1_8.text == 'date time':
                for each1 in mandatory_time:
                    if each == each1:
                        missingMandatory.append(each)
                        j += 1
            else:
                for each1 in mandatory_depth:
                    if each == each1:
                        missingMandatory.append(each)
                        j += 1
            if j == 0:
                missingOptional.append(each)
        missingOptional1 = set(missingOptional)
        missingMandatory1 = set(missingMandatory)

        if len(missingMandatory1) != 0:
            missingMandatoryString = ', '.join(missingMandatory1)
        else:
            missingMandatoryString = 'None'
        if len(missingOptional1) != 0:
            missingOptionalString = ', '.join(missingOptional1)
        else:
            missingOptionalString = 'None'

        line1 = Bs_data.find_all('mnemonicList')

        line2 = Bs_data.find_all('unitList')

        if len(line1) == len(line2):
            missing3 = 'Yes'
        else:
            missing3 = 'None'

        return stringfile, missingMandatoryString, missingOptionalString, missing3

    def dlistoxml(self, frame1, filename, uidWell, uidWellbore, BU, asset, purpose1, servicecompany, wellname1, idwi,
                  runid,
                  servicetype, datatype, uid):
        mandatory_time = ['name', 'indexType', 'minDateTimeIndex', 'maxDateTimeIndex', 'typeLogData', 'mnemonicList',
                          'unitList']
        mandatory_depth = ['name', 'indexType', 'minIndex', 'maxIndex', 'typeLogData', 'mnemonicList', 'unitList']

        wellname = wellname1
        wellbore = ''
        name = filename
        SC = servicecompany
        runNumber = ''
        creationDate = ''
        indexType = ''
        startDateTimeIndex = ''
        endDateTimeIndex = ''
        startIndex = ''
        endIndex = ''
        indexCurve = ''
        nullValue = ''
        description = str(purpose1)
        comments = 'BU: ' + str(BU) + '\nAsset:' + str(asset)
        servicecategory = str(idwi) + ',' + str(runid) + ',' + str(servicetype) + ',' + str(datatype)

        channels = str(frame1.channels)
        channels = channels.replace('[', '')
        channels = channels.replace(']', '')
        channels = channels.replace('Channel(', '')
        channels = channels.replace(')', '')
        mnemonicstring = channels
        mnemonicstring = mnemonicstring.replace(' ', '')
        mnemonic = mnemonicstring.split(',')

        units = []
        for channel in frame1.channels:
            units.append(channel.units)
        for unit in units:
            if unit == ' ':
                unit = 'unitless'
        unitstring = ','.join(str(v) for v in units)
        unitstring = unitstring.replace(" ", "")
        curves = frame1.curves()
        if str(frame1.index_type).lower().find(r'tim') != -1:
            indexType = 'date time'
            startDateTimeIndex = str(curves[mnemonic[0]][0])
            endDateTimeIndex = str(curves[mnemonic[0]][len(curves) - 1])
        elif str(frame1.index_type).lower().find(r'dept') != -1:
            indexType = 'measured depth'
            startIndex = str(curves[mnemonic[0]][0])
            endIndex = str(curves[mnemonic[0]][len(curves) - 1])

        indexCurve = str(mnemonic[0])
        top = Element('logs', xmlns="http://www.witsml.org/schemas/1series", version="1.4.1.1")
        top_1 = SubElement(top, 'log', uidWell=uidWell, uidWellbore=uidWellbore, uid=uid)
        top_1_1 = SubElement(top_1, 'nameWell')
        top_1_1.text = wellname
        top_1_2 = SubElement(top_1, 'nameWellbore')
        top_1_2.text = wellbore
        top_1_3 = SubElement(top_1, 'name')
        top_1_3.text = name
        top_1_4 = SubElement(top_1, 'serviceCompany')
        top_1_4.text = SC
        top_1_5 = SubElement(top_1, 'runNumber')
        top_1_5.text = runNumber
        top_1_6 = SubElement(top_1, 'creationDate')
        top_1_6.text = creationDate
        top_1_7 = SubElement(top_1, 'description')
        top_1_7.text = description
        top_1_8 = SubElement(top_1, 'indexType')
        top_1_8.text = indexType
        if indexType == 'date time':
            top_1_9 = SubElement(top_1, 'startDateTimeIndex')
            top_1_9.text = str(startDateTimeIndex)
            top_1_10 = SubElement(top_1, 'endDateTimeIndex')
            top_1_10.text = str(endDateTimeIndex)
        else:
            top_1_9a = SubElement(top_1, 'startIndex')
            top_1_9a.text = str(startIndex)
            top_1_10a = SubElement(top_1, 'endIndex')
            top_1_10a.text = str(endIndex)
        top_1_11 = SubElement(top_1, 'indexCurve')
        top_1_11.text = indexCurve
        top_1_12 = SubElement(top_1, 'nullValue')
        top_1_12.text = str(nullValue)
        j = 1
        for mnem in mnemonic:
            top_2 = SubElement(top_1, 'logCurveInfo', uid=mnem)
            child1 = SubElement(top_2, 'mnemonic')
            child1.text = str(mnem)
            child1a = SubElement(top_2, 'unit')
            child1a.text = str(units[j - 1])
            if indexType == 'date time':
                child2 = SubElement(top_2, 'minDateTimeIndex')
                child2.text = str(startDateTimeIndex)
                child3 = SubElement(top_2, 'maxDateTimeIndex')
                child3.text = str(endDateTimeIndex)
            child4 = SubElement(top_2, 'curveDescription')
            child4.text = ''
            child4a = SubElement(top_2, 'dataSource')
            child4a.text = ''
            child5 = SubElement(top_2, 'typeLogData')
            if str(mnem).lower().find('time') != -1:
                child5.text = 'date time'
            else:
                child5.text = 'double'
            j += 1
        top_3 = SubElement(top_1, 'logData')
        top_3_1 = SubElement(top_3, 'mnemonicList')
        top_3_1.text = mnemonicstring
        top_3_2 = SubElement(top_3, 'unitList')
        top_3_2.text = unitstring
        for curve in curves:
            top_3_3 = SubElement(top_3, 'data')
            x = ','.join(str(v) for v in curve)
            x1 = x.find(',')
            x2 = x[x1 + 1:]
            top_3_3.text = x2

        top_4 = SubElement(top_1, 'commonData')
        top_4_1 = SubElement(top_4, 'dTimCreation')
        date1 = str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])
        date1 += '+00:00'
        top_4_1.text = date1
        top_4_2 = SubElement(top_4, 'comments')
        top_4_2.text = comments
        top_4_3 = SubElement(top_4, 'serviceCategory')
        top_4_3.text = servicecategory

        stringfile = self.prettify(top)
        # tree = ElementTree(top)
        # tree.write(os.path.expanduser("~/Desktop/filename1.xml"))

        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
        desktop = os.path.expanduser("generatedXML/" + str(dt_string) + '.xml')
        with open(desktop, "w") as f:
            f.write(stringfile)

        missingData = []
        lst = top.findall('log/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('commonData/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('logCurveInfo/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        lst = top.findall('logData/')
        for item in lst:
            if item.text == '':
                missingData.append(item.tag)

        # missing = ', '.join(missingData)

        missingMandatory = []
        missingOptional = []

        for each in missingData:
            j = 0
            if indexType == 'date time':
                for each1 in mandatory_time:
                    if each == each1:
                        missingMandatory.append(each)
                        j += 1
            else:
                for each1 in mandatory_depth:
                    if each == each1:
                        missingMandatory.append(each)
                        j += 1
            if j == 0:
                missingOptional.append(each)
        missingOptional1 = set(missingOptional)
        missingMandatory1 = set(missingMandatory)

        if len(missingMandatory1) != 0:
            missingMandatoryString = ', '.join(missingMandatory1)
        else:
            missingMandatoryString = 'None'
        if len(missingOptional1) != 0:
            missingOptionalString = ', '.join(missingOptional1)
        else:
            missingOptionalString = 'None'

        if len(mnemonic) == len(units):
            missing3 = 'Yes'
        else:
            missing3 = 'None'

        return stringfile, missingMandatoryString, missingOptionalString, missing3

    pass


class APISupplementary:
    """Functions to support application interface"""

    def uploadedpage(self, index1, index2):
        # determine HTML template for visualization, depends on the index type [ buttons 'Visualize vs. Depth', ...]
        if index1 is not None and index2 is not None:
            template = 'uploaded.html'
        elif index1 is not None:
            template = 'uploadedTIME.html'
        elif index2 is not None:
            template = 'uploadedDEPTH.html'
        else:
            template = 'uploaded_base.html'
        return template

    def uploadedpageXML(self, index1, index2):
        # determine HTML template for visualization, depends on the index type [ buttons 'Visualize vs. Depth', ...]
        if index1 is not None and index2 is not None:
            template = 'uploaded1.html'
        elif index1 is not None:
            template = 'uploadedTIME1.html'
        elif index2 is not None:
            template = 'uploadedDEPTH1.html'
        else:
            template = 'uploaded1_base.html'
        return template

    pass

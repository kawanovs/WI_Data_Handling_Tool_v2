import os
import uuid
import lasio
from dlisio import dlis
from flask import render_template, Flask, session, request
from werkzeug.utils import redirect, secure_filename
import pandas as pd
import datetime

from classes import CSVprocessing, IndexType, APISupplementary, DLISprocessing, Visualization, XmlGeneration, \
    Configuration, CheckFunctions, InputXMLprocessing, LASprocessing
from forms import UploadForm, VisualizeCsvForm, DLISForm, Credentials, Credentials1, TestForm

# application set up
app = Flask('__name__')
# configure upload folder
app.config['UPLOAD_PATH'] = 'uploads'
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
# clear folders
for root, dirs, files in os.walk(app.config['UPLOAD_PATH']):
    for file in files:
        os.remove(os.path.join(root, file))
for root, dirs, files in os.walk('errorlog'):
    for file in files:
        os.remove(os.path.join(root, file))
for root, dirs, files in os.walk('generatedXML'):
    for file in files:
        os.remove(os.path.join(root, file))


@app.route('/', methods=['GET', 'POST'])
# upload page
def upload():
    form1 = UploadForm()

    if form1.validate_on_submit():
            # filename = secure_filename(form1.file.data.filename)
            # form1.file.data.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            # return render_template('uploaded.html')

        filename = secure_filename(form1.filename.data)
        type1 = form1.filetype.data
        # servicecompany = form1.servicecompany.data
        # BU = form1.BU.data
        # asset = form1.asset.data
        # wellname = form1.wellname.data
        # wellborename = form1.wellborename.data
        # how to represent values at constant depth
        # repr = form1.represent.data
        # filename = form1.file.raw_data[0].filename

        form1.file.data.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        session['filename'] = filename
        session['type1'] = type1
        # session['servicecompany'] = servicecompany
        # session['BU'] = BU
        # session['asset'] = asset
        # session['wellname'] = wellname
        # session['wellborename'] = wellborename
        # session['type1'] = type1
        # session['repr'] = repr

        if type1 == 'csv':
            # format csv
            return redirect('/csv')
        else:
            return redirect('/uploaded')

    return render_template('upload.html', form=form1)




@app.route('/csv', methods=['GET', 'POST'])
# formatting CSV because header position is not fixed
def csvhandling():
    filename = session.get('filename', None)
    data = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], filename))
    df0 = pd.DataFrame(data)
    df1 = CSVprocessing().csvpreprocess(df0)

    # create a row number column
    df1.insert(loc=0, column='Row number', value=df1.index)
    form = VisualizeCsvForm()

    if form.validate_on_submit():
        # row with column headings
        columnHeadingsRow = form.columns.data
        # row with measurement units
        unitsRow = form.measure.data
        # row where data starts
        dataStartRow = form.start.data

        session['columnHeadingsRow'] = columnHeadingsRow
        session['unitsRow'] = unitsRow
        session['dataStartRow'] = dataStartRow

        return redirect('/uploaded')

    return render_template('csvhandle.html', column_names=df1.columns,
                           row_data=list(df1.iloc[:20].values), zip=zip, form=form)


@app.route('/uploaded', methods=['GET', 'POST'])
def uploaded():
    # print(1)
    form3 = TestForm()
    filename = session.get('filename')
    type1 = session.get('type1')
    wellname = ''
    wellborename = ''
    servicecompany = ''
    runNumber = ''
    creationDate = ''
    indexType = ''
    startDateTimeIndex = ''
    endDateTimeIndex = ''
    indexCurve = ''
    nullValue = ''
    startIndex = ''
    endIndex = ''
    direction = ''
    dataSize = ''
    asset = ''
    BU = ''

    if type1 == 'las':
        # Read las file
        lf = lasio.read(os.path.join(app.config['UPLOAD_PATH'], filename), null_policy='all')

        # find index type for visualization templates
        indextype, index1, index2 = IndexType().findindex(lf, type1)

        dataSize = lf.data.shape[0]

        for well in lf.well:
            if well.descr.lower().find('null') != -1:
                nullValue = well.value
            elif well.descr.lower().find('company') != -1:
                BU = well.value
            elif well.descr.lower().find('well') != -1:
                wellname = well.value
            elif well.descr.lower().find('field') != -1:
                asset = well.value
            elif well.descr.lower().find('wellbore') != -1:
                wellborename = well.value
            elif well.descr.lower().find('service company') != -1:
                servicecompany = well.value
            elif well.descr.lower().find('run number') != -1:
                runNumber = well.value
            elif well.descr.lower().find('date') != -1 or well.descr.lower().find('date1') != -1:
                creationDate = well.value

        if lf.curves[0].descr.lower().find('dept') != -1:
            indexCurve = lf.curves[0].mnemonic
            indexType = 'measured depth'
            startIndex = lf.curves[0].data[0]
            endIndex = lf.curves[0].data[len(lf.curves[0]) - 1]
            if (float(startIndex) - float(endIndex)) > 0:
                direction = 'decreasing'
            elif (float(startIndex) - float(endIndex)) < 0:
                direction = 'increasing'
            else:
                direction = 'not included'
        elif lf.curves[0].descr.lower().find('time') != -1:
            indexCurve = lf.curves[0].mnemonic
            indexType = 'date time'
            startDateTimeIndex = lf.curves[0].data[0]
            endDateTimeIndex = lf.curves[0].data[len(lf.curves[0]) - 1]
            timedelta = (datetime.datetime.strptime(startDateTimeIndex, "%Y-%m-%dT%H:%M:%S.%f-05:00") -\
            datetime.datetime.strptime(endDateTimeIndex, "%Y-%m-%dT%H:%M:%S.%f-05:00"))
            if timedelta.days < 0 or timedelta.seconds < 0:
                direction = 'increasing'
            elif timedelta.days > 0 and timedelta.seconds > 0:
                direction = 'decreasing'
            else:
                direction = 'not included'


        if str(lf.curves[0].mnemonic).lower().find(r'tim') != -1:
            indexmain = 'Time'
        elif str(lf.curves[0].mnemonic).lower().find(r'dep') != -1:
            indexmain = 'Depth'
        if index1 is None or index2 is None:
            operation = 'Impossible to detect'
        else:
            RIH, POOH = LASprocessing().splitlogs(lf, repr)
            if len(RIH) != 0 and len(POOH) == 0:
                operation = 'RIH'
            elif len(RIH) == 0 and len(POOH) != 0:
                operation = 'POOH'
            else:
                operation = 'RIH and POOH'
        session['operation'] = operation

        # General Information
        data = [['File Name', filename], ['File Type', type1], ['Index Type', indexmain],
                 ['Number of Curves', len(lf.curves)], ['Operation', operation], ['Data nodes', dataSize]]
        df = pd.DataFrame(data=data, columns=['Parameter', 'Populated'])
        # File  Information
        data1 = [['Well name', wellname], ['Wellbore name', wellborename], ['Business Unit', BU],
                 ['Field', asset], ['Service Company', servicecompany], ['Run Number', runNumber],
                 ['Creation Date', creationDate], ['Null Value', nullValue], ['Direction', direction]]
        df1 = pd.DataFrame(data=data1, columns=['Parameter', 'Populated'])
        # which template to show
        template = APISupplementary().uploadedpage(index1, index2)

        if request.method == 'POST':

            df2 = pd.DataFrame(form3.data['images'])
            if df2.values[0][0] == '':
                session['wellname'] = df1.values[0][1]
            else:
                session['wellname'] = df2.values[0][0]
            if df2.values[1][0] == '':
                session['wellborename'] = df1.values[1][1]
            else:
                session['wellborename'] = df2.values[1][0]
            if df2.values[2][0] == '':
                session['Business Unit'] = df1.values[2][1]
            else:
                session['Business Unit'] = df2.values[2][0]
            if df2.values[3][0] == '':
                session['Field'] = df1.values[3][1]
            else:
                session['Field'] = df2.values[3][0]
            if df2.values[4][0] == '':
                session['Service Company'] = df1.values[4][1]
            else:
                session['Service Company'] = df2.values[4][0]
            if df2.values[5][0] == '':
                session['Run Number'] = df1.values[5][1]
            else:
                session['Run Number'] = df2.values[5][0]
            if df2.values[6][0] == '':
                session['Creation Date'] = df1.values[6][1]
            else:
                session['Creation Date'] = df2.values[6][0]
            if df2.values[7][0] == '':
                session['Null Value'] = df1.values[7][1]
            else:
                session['Null Value'] = df2.values[7][0]
            if df2.values[8][0] == '':
                session['Direction'] = df1.values[8][1]
            else:
                session['Direction'] = df2.values[8][0]

            session['indexType'] = indexType
            session['startDateTimeIndex'] = startDateTimeIndex
            session['endDateTimeIndex'] = endDateTimeIndex
            session['indexCurve'] = indexCurve
            session['nullValue'] = nullValue
            session['startIndex'] = startIndex
            session['endIndex'] = endIndex
            session['dataSize'] = dataSize


            return redirect('/export')

        return render_template(template, column_names=df.columns,
                               row_data=list(df.values), zip=zip, column_names1=df1.columns,
                               row_data1=list(df1.values), zip1=zip, form=form3)
    elif type1 == 'csv':
        data = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], filename))
        df0 = pd.DataFrame(data)

        columnHeadingsRow = session.get('columnHeadingsRow', None)
        unitsRow = ''
        dataStartRow = int(session.get('dataStartRow'))

        df2 = CSVprocessing().csvcolumns(df0, columnHeadingsRow, unitsRow, dataStartRow)
        dataSize = df2.shape[0]

        # index type
        indextype, index1, index2 = IndexType().findindex(df2, type1)

        for col in df2.columns:
            if col.lower().find('dept') != -1:
                indexCurve = col
                indexType = 'measured depth'
                startIndex = str(df2[col].iloc[0])
                endIndex = str(df2[col].iloc[len(df2) - 1])
                break
            elif col.lower().find('time') != -1:
                indexCurve = col
                indexType = 'date time'
                startDateTimeIndex = str(df2[col].iloc[0])
                endDateTimeIndex = str(df2[col].iloc[len(df2) - 1])
                break

        if df2.columns[0].lower().find('dept') != -1:
            indexCurve = df2.columns[0]
            indexType = 'measured depth'
            startIndex = df2[df2.columns[0]].iloc[0]
            endIndex = df2[df2.columns[0]].iloc[-1]
            if (float(startIndex) - float(endIndex)) > 0:
                direction = 'decreasing'
            elif (float(startIndex) - float(endIndex)) < 0:
                direction = 'increasing'
            else:
                direction = 'not included'
        elif df2.columns[0].lower().find('time') != -1:
            indexCurve = df2.columns[0]
            indexType = 'date time'
            startDateTimeIndex = df2[df2.columns[0]].iloc[0]
            endDateTimeIndex = df2[df2.columns[0]].iloc[-1]
            timedelta = (datetime.datetime.strptime(startDateTimeIndex, "%Y-%m-%dT%H:%M:%S.%f-05:00") -\
            datetime.datetime.strptime(endDateTimeIndex, "%Y-%m-%dT%H:%M:%S.%f-05:00"))
            if timedelta.days < 0 or timedelta.seconds < 0:
                direction = 'increasing'
            elif timedelta.days > 0 and timedelta.seconds > 0:
                direction = 'decreasing'
            else:
                direction = 'not included'

        # determine operation type - RIH/POOH
        operation = CSVprocessing().operationDefine(index1, index2, df2)
        session['operation'] = operation
        # dataframe for file information
        data = [['File Name', filename], ['File Type', type1], ['Index Type', indextype],
                 ['Number of Curves', len(df2.columns)],
                 ['Operation', operation], ['Data nodes', dataSize]]
        df = pd.DataFrame(data=data, columns=['Parameter', 'Value'])

        data1 = [['Well name', wellname], ['Wellbore name', wellborename], ['Business Unit', BU],
                 ['Field', asset], ['Service Company', servicecompany], ['Run Number', runNumber],
                 ['Creation Date', creationDate], ['Null Value', nullValue], ['Direction', direction]]
        df1 = pd.DataFrame(data=data1, columns=['Parameter', 'Populated'])

        template = APISupplementary().uploadedpage(index1, index2)

        if request.method == 'POST':

            df3 = pd.DataFrame(form3.data['images'])

            session['wellname'] = df3.values[0][0]
            session['wellborename'] = df3.values[1][0]
            session['Business Unit'] = df3.values[2][0]
            session['Field'] = df3.values[3][0]
            session['Service Company'] = df3.values[4][0]
            session['Run Number'] = df3.values[5][0]
            session['Creation Date'] = df3.values[6][0]
            session['Null Value'] = df3.values[7][0]

            if df3.values[8][0] == '':
                session['Direction'] = df1.values[8][1]
            else:
                session['Direction'] = df3.values[8][0]

            session['indexType'] = indexType
            session['startDateTimeIndex'] = startDateTimeIndex
            session['endDateTimeIndex'] = endDateTimeIndex
            session['indexCurve'] = indexCurve
            session['nullValue'] = nullValue
            session['startIndex'] = startIndex
            session['endIndex'] = endIndex
            session['dataSize'] = dataSize


            return redirect('/export')


        return render_template(template, column_names=df.columns,
                               row_data=list(df.values), zip=zip, column_names1=df1.columns,
                               row_data1=list(df1.values), zip1=zip, form=form3)
    elif type1 == 'dlis':
        f, *tail = dlis.load(os.path.join(app.config['UPLOAD_PATH'], filename))

        indextype1, channelsnumber, ops = DLISprocessing().dlisInfo(f)
        data1 = [['File Name', filename], ['File Type', type1], ['Index Type', ', '.join(indextype1)],
                 ['Frames', len(f.frames)],
                 ['Number of Curves', channelsnumber],
                 ['Operation', ', '.join(ops)]]
        session['operation'] = ', '.join(ops)
        df1 = pd.DataFrame(data=data1, columns=['Parameter', 'Value'])
        indextype, index1, index2 = IndexType().findindex(f, type1)
        template = APISupplementary().uploadedpage(index1, index2)
        return render_template(template, column_names=df.columns,
                               row_data=list(df.values), zip=zip, column_names1=df1.columns,
                               row_data1=list(df1.values), zip1=zip)
    elif type1 == 'xml':
        f = open(os.path.join(app.config['UPLOAD_PATH'], filename), 'r')
        data1 = f.read()
        f.close()

        curvesnumber1 = InputXMLprocessing().curvesnumber(data1)
        indextype, index1, index2 = IndexType().findindex(data1, type1)
        df2 = InputXMLprocessing().dataframeFromXml(data1)
        operation = CSVprocessing().operationDefine(index1, index2, df2)
        session['operation'] = operation
        data1 = [['File Name', filename], ['File Type', type1], ['Index Type', indextype],
                 ['Number of Curves', curvesnumber1], ['Operation', operation]]

        df1 = pd.DataFrame(data=data1, columns=['Parameter', 'Value'])
        template = APISupplementary().uploadedpage(index1, index2)
        return render_template(template, column_names=df.columns,
                               row_data=list(df.values), zip=zip, column_names1=df1.columns,
                               row_data1=list(df1.values), zip1=zip)


@app.route('/visual/')
# visualize from Time
def my_dash_app():
    filename = session.get('filename')
    type1 = session.get('type1')
    repr = session.get('repr', None)

    if type1 == 'las':
        lf = lasio.read(os.path.join(app.config['UPLOAD_PATH'], filename), null_policy='all')
        timemnem = IndexType().LASmnemonic('Time', lf)
        chart = Visualization().generate_curvesTime(lf, timemnem)
        return render_template('dashboard.html', plot=chart)
    elif type1 == 'csv':
        data = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], filename))
        df = pd.DataFrame(data)
        columnHeadingsRow = session.get('columnHeadingsRow', None)
        unitsRow = int(session.get('unitsRow', None))
        dataStartRow = int(session.get('dataStartRow'))
        df2 = CSVprocessing().csvcolumns(df, columnHeadingsRow, unitsRow, dataStartRow)
        df2 = CSVprocessing().csvnumeric(df2)
        print(df2)
        chart = Visualization().generate_curvesCSV(df2)
        return render_template('dashboard.html', plot=chart)
    elif type1 == 'dlis':
        f, *tail = dlis.load(os.path.join(app.config['UPLOAD_PATH'], filename))
        j = 0
        for frame in f.frames:
            if str(frame.index_type).lower().find(r'tim') != -1:
                j += 1
        if j == 0:
            return redirect('/error')
    elif type1 == 'xml':
        f = open(os.path.join(app.config['UPLOAD_PATH'], filename), 'r')
        data1 = f.read()
        df = InputXMLprocessing().dataframeFromXml(data1)
        chart = Visualization().generate_curvesCSV(df)
        return render_template('dashboard.html', plot=chart)


@app.route('/visualdepth/', methods=['GET', 'POST'])
# visualize from Depth
def my_dash_app2():
    filename = session.get('filename', None)
    type1 = session.get('type1', None)
    repr = session.get('repr', None)

    if type1 == 'csv':
        data = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], filename))
        df = pd.DataFrame(data)
        columnHeadingsRow = session.get('columnHeadingsRow', None)
        unitsRow = int(session.get('unitsRow', None))
        dataStartRow = int(session.get('dataStartRow'))
        df2 = CSVprocessing().csvcolumns(df, columnHeadingsRow, unitsRow, dataStartRow)
        df2 = CSVprocessing().csvnumeric(df2)
        if repr == 'Average value':
            RIH, POOH = CSVprocessing().splitlogs(df2, 'mean')
        elif repr == 'Minimum value':
            RIH, POOH = CSVprocessing().splitlogs(df2, 'min')
        else:
            RIH, POOH = CSVprocessing().splitlogs(df2, 'max')
        if len(RIH) != 0 and len(POOH) != 0:
            return redirect('/RIH')
        else:
            chart = Visualization().generate_curvesDepthCSV(df2)
            return render_template('dashboard.html', plot=chart)
    elif type1 == 'xml':
        f = open(os.path.join(app.config['UPLOAD_PATH'], filename), 'r')
        data1 = f.read()
        df = InputXMLprocessing().dataframeFromXml(data1)

        if repr == 'Average value':
            RIH, POOH = CSVprocessing().splitlogs(df, 'mean')
        elif repr == 'Minimum value':
            RIH, POOH = CSVprocessing().splitlogs(df, 'min')
        else:
            RIH, POOH = CSVprocessing().splitlogs(df, 'max')
        if len(RIH) != 0 and len(POOH) != 0:
            return redirect('/RIH')
        else:
            chart = Visualization().generate_curvesDepthCSV(df)
            return render_template('dashboard.html', plot=chart)
    elif type1 == 'las':
        lf = lasio.read(os.path.join(app.config['UPLOAD_PATH'], filename), null_policy=['999.25'])
        RIH, POOH = LASprocessing().splitlogs(lf, repr)
        if len(RIH) == 0 or len(POOH) == 0:
            depthmnem = IndexType().LASmnemonic('Depth', lf)
            chart = Visualization().generate_curves(lf, depthmnem)
            return render_template('dashboard.html', plot=chart)
        else:
            redirect('/RIH')
    elif type1 == 'dlis':
        f, *tail = dlis.load(os.path.join(app.config['UPLOAD_PATH'], filename))
        form1 = DLISForm()
        # choices for SelectField - depend on Frames in DLIS
        choices1 = []
        for i in range(len(f.frames)):
            choices1.append((i + 1, str(f.frames[i])))
        form1.frameNumber.choices = choices1
        # DLIS channels summary for visualization
        channels = CSVprocessing().summary_dataframe(f.channels, name='Name', long_name='Long Name',
                                                     dimension='Dimension', units='Units', frame='Frame')
        a = channels['Dimension'].tolist()
        b = []
        for i in range(len(a)):
            if a[i] == [1]:
                b.append('Yes')
            else:
                b.append('No')
        channels1 = pd.DataFrame()
        channels1['Frame'] = channels['Frame'].astype('str')
        channels1['Name'] = channels['Long Name']
        channels1['Units'] = channels['Units']
        channels1['Plottable?'] = b
        channels1 = channels1.sort_values(by=['Frame'])
        if form1.validate_on_submit():
            frame_needed = form1.frameNumber.data
            for i in range(len(choices1)):
                if choices1[i][0] == frame_needed:
                    frame_needed1 = choices1[i][1]
            session['frame_needed1'] = frame_needed1
            return redirect('/DLISdepth')
        return render_template('uploadedDLIS.html', column_names=channels1.columns,
                               row_data=list(channels1.values), zip=zip, form=form1)


@app.route('/DLISdepth')
def dlislis():
    filename = session.get('filename', None)
    framenumber = session.get('frame_needed1', None)
    f, *tail = dlis.load(os.path.join(app.config['UPLOAD_PATH'], filename))
    x = str(framenumber).find('(')
    x1 = str(framenumber).find(')')
    framename = str(framenumber)[x + 1:x1]

    frame1 = f.object('FRAME', framename)
    chart = Visualization().curvesDepthDLIS(frame1)
    return render_template('dashboardDLIS.html', plot=chart)


@app.route('/RIH')
def rih():
    type1 = session.get('type1', None)
    filename = session.get('filename', None)
    repr = session.get('repr', None)
    if type1 == 'csv':
        data = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], filename))
        df = pd.DataFrame(data)

        columnHeadingsRow = session.get('columnHeadingsRow', None)
        unitsRow = int(session.get('unitsRow', None))
        dataStartRow = int(session.get('dataStartRow'))

        df2 = CSVprocessing().csvcolumns(df, columnHeadingsRow, unitsRow, dataStartRow)
        df2 = CSVprocessing().csvnumeric(df2)

        for col in df2.columns:
            if str(col).lower().find(r'tim') != -1:
                col1 = col
        df2 = df2.drop(col1, axis=1)
        df2 = df2.reset_index(drop=True)

        if repr == 'Average value':
            RIH, POOH = CSVprocessing().splitlogs(df2, 'mean')
        elif repr == 'Minimum value':
            RIH, POOH = CSVprocessing().splitlogs(df2, 'min')
        else:
            RIH, POOH = CSVprocessing().splitlogs(df2, 'max')
        RIH1 = pd.DataFrame(data=RIH, columns=df2.columns)
        chart = Visualization().generate_curvesDepthCSV(RIH1)
        return render_template('dashboardcsv.html', plot=chart)

    elif type1 == 'xml':
        f = open(os.path.join(app.config['UPLOAD_PATH'], filename), 'r')
        data1 = f.read()
        df = InputXMLprocessing().dataframeFromXml(data1)

        if repr == 'Average value':
            RIH, POOH = CSVprocessing().splitlogs(df, 'mean')
        elif repr == 'Minimum value':
            RIH, POOH = CSVprocessing().splitlogs(df, 'min')
        else:
            RIH, POOH = CSVprocessing().splitlogs(df, 'max')
        RIH1 = pd.DataFrame(data=RIH, columns=df.columns)
        chart = Visualization().generate_curvesDepthCSV(RIH1)
        return render_template('dashboardcsv.html', plot=chart)
    elif type1 == 'las':
        lf = lasio.read(os.path.join(app.config['UPLOAD_PATH'], filename), null_policy=['999.25'])
        if repr == 'Average value':
            RIH, POOH = LASprocessing().splitlogs(lf, 'mean')
        elif repr == 'Minimum value':
            RIH, POOH = LASprocessing().splitlogs(lf, 'min')
        else:
            RIH, POOH = LASprocessing().splitlogs(lf, 'max')
        df1 = lf.df()
        for col in df1.columns:
            if str(col).lower().find(r'tim') != -1:
                col1 = col
                pass
        df1 = df1.drop(col1, axis=1)
        df1 = df1.reset_index()
        RIH1 = pd.DataFrame(data=RIH, columns=df1.columns)
        chart = Visualization().generate_curvesDepthCSV(RIH1)
        return render_template('dashboardcsv.html', plot=chart)


@app.route('/POOH')
def pooh():
    filename = session.get('filename', None)
    type1 = session.get('type1', None)
    repr = session.get('repr', None)
    if type1 == 'csv':
        data = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], filename))
        df = pd.DataFrame(data)
        columnHeadingsRow = session.get('columnHeadingsRow', None)
        unitsRow = int(session.get('unitsRow', None))
        dataStartRow = int(session.get('dataStartRow'))

        df2 = CSVprocessing().csvcolumns(df, columnHeadingsRow, unitsRow, dataStartRow)
        df2 = CSVprocessing().csvnumeric(df2)
        for col in df2.columns:
            if str(col).find('Time') != -1:
                col1 = col
        df2 = df2.drop(col1, axis=1)
        df2 = df2.reset_index(drop=True)
        repr = session.get('repr', None)
        if repr == 'Average value':
            RIH, POOH = CSVprocessing().splitlogs(df2, 'mean')
        elif repr == 'Minimum value':
            RIH, POOH = CSVprocessing().splitlogs(df2, 'min')
        else:
            RIH, POOH = CSVprocessing().splitlogs(df2, 'max')
        POOH1 = pd.DataFrame(data=POOH, columns=df2.columns)
        chart = Visualization().generate_curvesDepthCSV(POOH1)
        return render_template('dashboardcsv1.html', plot=chart)
    elif type1 == 'xml':
        f = open(os.path.join(app.config['UPLOAD_PATH'], filename), 'r')
        data1 = f.read()
        df = InputXMLprocessing().dataframeFromXml(data1)
        repr = session.get('repr', None)

        if repr == 'Average value':
            RIH, POOH = CSVprocessing().splitlogs(df, 'mean')
        elif repr == 'Minimum value':
            RIH, POOH = CSVprocessing().splitlogs(df, 'min')
        else:
            RIH, POOH = CSVprocessing().splitlogs(df, 'max')
        POOH1 = pd.DataFrame(data=POOH, columns=df.columns)
        chart = Visualization().generate_curvesDepthCSV(POOH1)
        return render_template('dashboardcsv1.html', plot=chart)
    elif type1 == 'las':
        lf = lasio.read(os.path.join(app.config['UPLOAD_PATH'], filename), null_policy=['999.25'])
        if repr == 'Average value':
            RIH, POOH = LASprocessing().splitlogs(lf, 'mean')
            print(len(RIH), len(POOH))
        elif repr == 'Minimum value':
            RIH, POOH = LASprocessing().splitlogs(lf, 'min')
        else:
            RIH, POOH = LASprocessing().splitlogs(lf, 'max')
        df1 = lf.df()
        for col in df1.columns:
            if str(col).lower().find(r'tim') != -1:
                col1 = col
                pass
        df1 = df1.drop(col1, axis=1)
        df1 = df1.reset_index()
        POOH1 = pd.DataFrame(data=RIH, columns=df1.columns)
        chart = Visualization().generate_curvesDepthCSV(POOH1)
        return render_template('dashboardcsv1.html', plot=chart)


@app.route('/check')
def checking():
    filename = session.get('filename', None)
    type1 = session.get('type1', None)
    servicecompany = session.get('servicecompany')
    BU = session.get('BU')
    asset = session.get('asset')
    wellname = session.get('wellname')
    operation = session.get('operation')
    data = [['Business Unit', BU], ['Asset', asset],
            ['Service Company', servicecompany], ['Well', wellname]]
    generalInfo = pd.DataFrame(data=data)
    if type1 == 'dlis':
        dlisIndexType = session.get('dlisIndexType', None)
        f, *tail = dlis.load(os.path.join(app.config['UPLOAD_PATH'], filename))
        channels = CSVprocessing().summary_dataframe(f.channels, name='Name', long_name='Long Name',
                                                     dimension='Dimension', units='Units', frame='Frame')
        channels1 = pd.DataFrame()

        channels1['Frame'], channels1['Name'], channels1['Units'] = channels['Frame'].astype('str'), channels['Name'], \
                                                                    channels['Units']
        channels1['Name'] = channels['Name']
        mnemonicslist = channels['Name'].to_list()

        dataframe1 = Configuration().KDIunits()
        recognized = []
        k = 0
        for i in range(len(channels1)):
            j = 0
            for p in range(len(dataframe1)):
                if dataframe1['Units'].iloc[p] == channels1['Units'].iloc[i]:
                    recognized.append(dataframe1['Units'].iloc[p])
                    j += 1
            if j == 0:
                recognized.append('')
                k += 1
        channels1['KDI Units'] = recognized
        channels1 = channels1.sort_values(by=['Frame'])
        structure, equipment1, data1, runNumber1, Logname = CheckFunctions().checkdlisfunction(dlisIndexType,
                                                                                               mnemonicslist)
        channels1['Mnemonic Structure'] = structure
        channels1['Equipment Type'] = equipment1
        channels1['Data Type'] = data1
        channels1['Run Number'] = runNumber1
        channels1['Log Name'] = Logname

        indextype1, channelsnumber, ops = DLISprocessing().dlisInfo(f)
        data1 = [['File Name', filename], ['File Type', type1], ['Index Type', ', '.join(indextype1)],
                 ['Frames', len(f.frames)],
                 ['Number of Curves', channelsnumber],
                 ['Operation', ', '.join(ops)]]

        fileInfo = pd.DataFrame(data=data1, columns=['Parameter', 'Value'])

        result = CheckFunctions().dlistimestamp(f)
        description, serviceCategory, dataSource = CheckFunctions().dlisWDtags(f)
        d = {'Check': ['Timestamp', 'Description Tag', 'Service Category Tag', 'Data Source Tag'],
             'Result': [result, description, serviceCategory, dataSource]}
        df = pd.DataFrame(data=d)
        CheckFunctions().errorLog(generalInfo, fileInfo, df, channels1)

        return render_template('check.html', column_names1=df.columns,
                               row_data1=list(df.values), zip1=zip, column_names=channels1.columns,
                               row_data=list(channels1.values), zip=zip)
    elif type1 == 'las':
        lf = lasio.read(os.path.join(app.config['UPLOAD_PATH'], filename), null_policy='all')
        a1 = []
        for curve in lf.curves:
            a1.append([curve.descr, curve.mnemonic, curve.unit])
        summary = pd.DataFrame(data=a1, columns=['Curve', 'Mnemonic', 'Unit'])
        recognized = CheckFunctions().unitsrecognized(lf, 'las')
        summary['KDI Units'] = recognized
        summary['Mnemonic Structure'], summary['Equipment Type'], summary['Data Type'], summary['Run Number'], summary[
            'Log Name'] = CheckFunctions().checklasfunction(lf)
        result = CheckFunctions().lastimestamp(lf)
        description, serviceCategory, dataSource = CheckFunctions().lasWDtags(lf)
        d = {'Check': ['Timestamp', 'Description Tag', 'Service Category Tag', 'Data Source Tag'],
             'Result': [result, description, serviceCategory, dataSource]}
        df = pd.DataFrame(data=d)

        if str(lf.curves[0].mnemonic).lower().find(r'tim'):
            indexmain = 'Time'
        elif str(lf.curves[0].mnemonic).lower().find(r'dep'):
            indexmain = 'Depth'

        data1 = [['File Name', filename], ['File Type', type1], ['Index Type', indexmain],
                 ['Number of Curves', len(lf.curves)], ['Operation', operation]]
        fileInfo = pd.DataFrame(data=data1, columns=['Parameter', 'Value'])

        CheckFunctions().errorLog(generalInfo, fileInfo, df, summary)
        return render_template('check.html', column_names1=df.columns,
                               row_data1=list(df.values), zip1=zip, column_names=summary.columns,
                               row_data=list(summary.values), zip=zip)

    elif type1 == 'csv':
        data = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], filename))
        df = pd.DataFrame(data)
        columnHeadingsRow = session.get('columnHeadingsRow', None)
        unitsRow = int(session.get('unitsRow', None))
        dataStartRow = int(session.get('dataStartRow'))

        df2 = CSVprocessing().csvcolumns(df, columnHeadingsRow, unitsRow, dataStartRow)
        indextype, index1, index2 = IndexType().findindex(df2, type1)

        if indextype == 'Depth':
            indexType = 'measured depth'
        elif indextype is not None:
            indexType = 'date time'
        else:
            indexType = None

        recognized, mnemoniclist, units = CheckFunctions().unitsrecognized(df2, type1)

        summary = pd.DataFrame()
        summary['Description'], summary['Units'], summary['KDI Unit'] = mnemoniclist, units, recognized
        summary['Mnemonic Structure'], summary['Equipment Type'], summary['Data Type'], summary['Run Number'], summary[
            'Log Name'] = CheckFunctions().checkcsvfunction(indexType, mnemoniclist)
        result = CheckFunctions().csvtimestamp(df2)
        description, serviceCategory, dataSource = CheckFunctions().csvWDtags(df2)
        d = {'Check': ['Timestamp', 'Description Tag', 'Service Category Tag', 'Data Source Tag'],
             'Result': [result, description, serviceCategory, dataSource]}
        df = pd.DataFrame(data=d)

        data1 = [['File Name', filename], ['File Type', type1], ['Index Type', indextype],
                 ['Number of Curves', len(df2.columns)],
                 ['Operation', operation]]
        fileInfo = pd.DataFrame(data=data1, columns=['Parameter', 'Value'])
        CheckFunctions().errorLog(generalInfo, fileInfo, df, summary)
        return render_template('check.html', column_names1=df.columns,
                               row_data1=list(df.values), zip1=zip, column_names=summary.columns,
                               row_data=list(summary.values), zip=zip)
    elif type1 == 'xml':
        f = open(os.path.join(app.config['UPLOAD_PATH'], filename), 'r')
        data1 = f.read()
        f.close()
        recognized, mnemoniclist, units = CheckFunctions().unitsrecognized(data1, type1)
        indextype, index1, index2 = IndexType().findindex(data1, type1)
        if indextype == 'Depth':
            indexType = 'measured depth'
        elif indextype == 'Time':
            indexType = 'date time'
        summary = pd.DataFrame()
        summary['Units'], summary['Description'], summary['KDI Unit'] = units, mnemoniclist, recognized
        summary['Mnemonic Structure'], summary['Equipment Type'], summary['Data Type'], summary['Run Number'], summary[
            'Log Name'] = CheckFunctions().checkcsvfunction(indexType, mnemoniclist)
        df2 = InputXMLprocessing().dataframeFromXml(data1)
        result = CheckFunctions().csvtimestamp(df2)
        description, serviceCategory, dataSource, resultik = CheckFunctions().xmlWDtags(data1)
        d = {'Check': ['Timestamp', 'Description Tag', 'Service Category Tag', 'Service Category Tag Structure',
                       'Data Source Tag', 'KDI requirements'],
             'Result': [result, description, serviceCategory, resultik, dataSource, CheckFunctions().xmlKDItags(data1)]}
        df = pd.DataFrame(data=d)

        data1 = [['File Name', filename], ['File Type', type1], ['Index Type', indextype],
                 ['Number of Curves', len(df2.columns)],
                 ['Operation', operation]]
        fileInfo = pd.DataFrame(data=data1, columns=['Parameter', 'Value'])
        CheckFunctions().errorLog(generalInfo, fileInfo, df, summary)
        return render_template('check.html', column_names1=df.columns,
                               row_data1=list(df.values), zip1=zip, column_names=summary.columns,
                               row_data=list(summary.values), zip=zip)


@app.route('/export', methods=['GET', 'POST'])
def export1():
    filename = session.get('filename', None)
    type1 = session.get('type1', None)
    BU = session.get('Business Unit')
    asset = session.get('Field')
    servicecompany = session.get('Service Company')
    wellname = session.get('wellname')
    wellborename = session.get('wellborename')
    direction = session['Direction']
    nullValue = session['Null Value']
    creationDate = session['Creation Date']
    runNumber = session['Run Number']
    indexType = session['indexType']
    startDateTimeIndex = session['startDateTimeIndex']
    endDateTimeIndex = session['endDateTimeIndex']
    indexCurve = session['indexCurve']
    startIndex = session['startIndex']
    endIndex = session['endIndex']
    dataSize = session['dataSize']


    if type1 == 'dlis':
        form2 = Credentials1()
        f, *tail = dlis.load(os.path.join(app.config['UPLOAD_PATH'], filename))
        choices1 = []
        for i in range(len(f.frames)):
            choices1.append((i + 1, str(f.frames[i])))
        form2.frameNumber.choices = choices1
        if form2.validate_on_submit():
            frame_needed = form2.frameNumber.data
            for i in range(len(choices1)):
                if choices1[i][0] == frame_needed:
                    frame_needed1 = choices1[i][1]
            uidwell1 = form2.uidwell.data
            uidwellbore1 = form2.uidwellbore.data
            uidWI1 = form2.uidwi.data
            runid1 = form2.runid.data
            servicetype = form2.servicetype.data
            datatype = form2.datatype.data
            purpose1 = form2.purpose1.data
            uid = form2.uid.data
            # generate uid?
            if uid:
                uid = str(uuid.uuid1())
            else:
                uid = ''
            x = str(frame_needed1).find('(')
            x1 = str(frame_needed1).find(')')
            framename = str(frame_needed1)[x + 1:x1]
            frame1 = f.object('FRAME', framename)
            xmlstring, missing1, missing2, missing3 = XmlGeneration().dlistoxml(frame1, filename, uidwell1,
                                                                                uidwellbore1, BU, asset,
                                                                                purpose1,
                                                                                servicecompany, wellname, uidWI1,
                                                                                runid1,
                                                                                servicetype,
                                                                                datatype, uid)
            return render_template('exporttoXML.html', string=xmlstring, missingData=missing1,
                                   missingData2=missing2,
                                   missingData3=missing3)
        return render_template('setupDLIStoXML.html', form=form2)
    else:
        form1 = Credentials()

        # if form1.validate_on_submit():
        if request.method == 'POST':
            uidwell1 = form1.uidwell.data
            uidwellbore1 = form1.uidwellbore.data
            uidWI1 = form1.uidwi.data
            # runid1 = form1.runid.data
            servicetype = form1.servicetype.data
            datatype = form1.datatype.data
            purpose1 = form1.purpose1.data
            uid = form1.uid.data
            # creationDate_manual = form1.creationDate_manual.data
            # splitSize = form1.splitSize.data
            datasource = form1.datasource.data
            # generate uid?
            if uid:
                uid = str(uuid.uuid1())
            else:
                uid = ''
            if type1 == 'las':
                lf = lasio.read(os.path.join(app.config['UPLOAD_PATH'], filename), null_policy='none')


                xmlstring, missing1, missing2, missing3 = XmlGeneration().lastoxml(lf, filename, uidwell1, uidwellbore1,
                                                                                   BU, asset,
                                                                                   purpose1,
                                                                                   servicecompany, wellname, uidWI1,
                                                                                   runNumber,
                                                                                   servicetype,
                                                                                   datatype, uid, creationDate,
                                                                                   wellborename,
                                                                                   direction,
                                                                                   datasource,
                                                                                   nullValue,
                                                                                   indexType,
                                                                                   startDateTimeIndex,
                                                                                   endDateTimeIndex,
                                                                                   indexCurve,
                                                                                   startIndex,
                                                                                   endIndex,
                                                                                   dataSize)

                return render_template('exporttoXML.html', string=xmlstring, missingData=missing1,
                                       missingData2=missing2,
                                       missingData3=missing3)
            elif type1 == 'csv':
                data = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], filename))
                df = pd.DataFrame(data)
                columnHeadingsRow = session.get('columnHeadingsRow', None)
                unitsRow = int(session.get('unitsRow', None))
                dataStartRow = int(session.get('dataStartRow'))

                df2 = CSVprocessing().csvcolumns(df, columnHeadingsRow, unitsRow, dataStartRow)
                # wellname = session.get('wellname', None)
                xmlstring, missing1, missing2, missing3 = XmlGeneration().csvtoxml(df, df2, columnHeadingsRow,
                                                                                   dataStartRow, filename, uidwell1,
                                                                                   uidwellbore1,
                                                                                   BU, asset, purpose1,
                                                                                   servicecompany, wellname, uidWI1,
                                                                                   runNumber,
                                                                                   servicetype,
                                                                                   datatype, uid, creationDate,
                                                                                   wellborename,
                                                                                   direction,
                                                                                   datasource,
                                                                                   nullValue,
                                                                                   indexType,
                                                                                   startDateTimeIndex,
                                                                                   endDateTimeIndex,
                                                                                   indexCurve,
                                                                                   startIndex,
                                                                                   endIndex,
                                                                                   dataSize)
                return render_template('exporttoXML.html', string=xmlstring, missingData=missing1,
                                       missingData2=missing2,
                                       missingData3=missing3)
            elif type1 == 'xml':
                f = open(os.path.join(app.config['UPLOAD_PATH'], filename), 'r')
                data1 = f.read()
                df = InputXMLprocessing().dataframeFromXml(data1)

                xmlstring, missing1, missing2, missing3 = XmlGeneration().xmltoxml(data1, uidwell1,
                                                                                   uidwellbore1,
                                                                                   BU, asset,
                                                                                   purpose1,
                                                                                   servicecompany, wellname, uidWI1,
                                                                                   runid1,
                                                                                   servicetype,
                                                                                   datatype, uid)
                return render_template('exporttoXML.html', string=xmlstring, missingData=missing1,
                                       missingData2=missing2,
                                       missingData3=missing3)
        return render_template('setupLAStoXML.html', form=form1)


@app.route('/units')
# SiteCom units
def units1():
    dataframe1 = pd.read_excel('configuration/KDIunits.xlsx', index_col=0)
    dataframe1.columns = ['Units', 'Description']
    return render_template('units.html', column_names=dataframe1.columns,
                           row_data=list(dataframe1.values), zip=zip)

if __name__ == "__main__":
   app.run()
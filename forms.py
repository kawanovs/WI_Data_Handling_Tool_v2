from flask_wtf import FlaskForm
from wtforms import StringField, FileField, validators, SubmitField, SelectField, BooleanField, FieldList, FormField
from wtforms.validators import InputRequired, Optional

from classes import Configuration


class UploadForm(FlaskForm):
    filename = StringField('Enter', [validators.DataRequired()])
    file = FileField()
    filetype = SelectField("File Type ", choices=[
        # (value, label)
        ("las", "las"),
        ("csv", "csv")])
        # ('dlis', 'dlis'),
        # ('xml', 'xml')])
    # filename = StringField('Enter', [validators.DataRequired()])
    # filetype = SelectField("File Type ", choices=[
    #     ("las", "las"),
    #     ("csv", "csv"),
    #     ('dlis', 'dlis'),
    #     ('xml', 'xml')])
    # servicecompany = StringField('Enter', [validators.DataRequired()])
    # BU = StringField('Enter', [validators.DataRequired()])
    # asset = StringField('Enter', [validators.DataRequired()])
    # wellname = StringField('Enter', validators=[InputRequired()])
    # wellborename = StringField('Enter', validators=[InputRequired()])
    # file = FileField()
    # representation of data points for equal depths
    # represent = SelectField("File Type ", choices=[
    #     ("Minimum value", "Minimum value"),
    #     ("Maximum value", "Maximum value"),
    #     ('Average value', 'Average value')])

class ImageForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(ImageForm, self).__init__(*args, **kwargs)
    # frequency = SelectField(choices=[('monthly', 'Monthly'), ('weekly', 'Weekly')])
    caption = StringField('Caption')
    # credit = StringField('Credit')


class TestForm(FlaskForm):
    images = FieldList(FormField(ImageForm), min_entries=9)


class VisualizeCsvForm(FlaskForm):
    columns = StringField('columns', render_kw={'placeholder': 'Optional'}, validators=[Optional()])
    start = StringField('start', [validators.DataRequired()])
    measure = StringField('measure', [validators.DataRequired()])


class DLISForm(FlaskForm):
    frameNumber = SelectField('Frame', choices=[], coerce=int)
    visual1 = SubmitField('Visualize')


class Credentials(FlaskForm):
    uidwell = StringField('uidwell', [validators.DataRequired()])
    uidwellbore = StringField('uidwellbore', [validators.DataRequired()])
    runid = StringField('runid', [validators.DataRequired()])
    uidwi = StringField('uiwdi', [validators.DataRequired()])
    purpose1 = StringField('purpose1', [validators.DataRequired()])
    ser, choices1 = Configuration().serviceTypeOptionsforXML()
    servicetype = SelectField("Service Type ", choices=choices1)
    ser1, choices1 = Configuration().dataTypeOptions()
    datatype = SelectField("Data Type ", choices=choices1)
    uid = BooleanField('uid')
    creationDate_manual = StringField('Log Creation Date', [validators.DataRequired()])
    splitSize = StringField('Split Size', [validators.DataRequired()])
    datasource = StringField('Data Source', [validators.DataRequired()])


class Credentials1(FlaskForm):
    uidwell = StringField('uidwell', [validators.DataRequired()])
    uidwellbore = StringField('uidwellbore', [validators.DataRequired()])
    runid = StringField('runid', [validators.DataRequired()])
    uidwi = StringField('uiwdi', [validators.DataRequired()])
    purpose1 = StringField('purpose1', [validators.DataRequired()])
    ser, choices1 = Configuration().serviceTypeOptionsforXML()
    servicetype = SelectField("Service Type ", choices=choices1)
    ser1, choices1 = Configuration().dataTypeOptions()
    datatype = SelectField("Data Type ", choices=choices1)
    uid = BooleanField('uid')
    frameNumber = SelectField('Frame', choices=[], coerce=int)
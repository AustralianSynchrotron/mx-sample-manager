from wtforms import Form, TextField, SelectField


class HolderForm(Form):
    name = TextField('Name')
    type = SelectField('Type', choices=[(u'Puck', 'Puck'), (u'Cassette', 'Cassette')])

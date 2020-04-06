"""This Admin class turns the background of a Person's first
name pink if its first name doesn't start with a capital"""

from camelot.core.qt import QtGui
from camelot.model.party import Person

def first_name_background_color(person):
    import string
    if person.first_name:
        if person.first_name[0] not in string.uppercase:
            return QtGui.QColor('pink')
    
class Admin(Person.Admin):
    field_attributes = {'first_name':{'background_color':first_name_background_color}}

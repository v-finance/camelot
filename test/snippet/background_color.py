"""This Admin class turns the background of a Person's first
name pink if its first starts with a capital M"""

from camelot.core.qt import QtGui
from camelot.model.party import Person

def first_name_background_color(person):
    if person.first_name is not None:
        if person.first_name.startswith('M'):
            return QtGui.QColor('pink')
    
class Admin(Person.Admin):
    field_attributes = {
        'first_name': {
            'background_color': first_name_background_color
        }
    }

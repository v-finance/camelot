"""This Admin class turns the background of a Person's first
name pink if its first name doesn't start with a capital"""

from PyQt4.QtGui import QColor

from camelot.model.party import Person

def first_name_background_color(person):
    import string
    if person.first_name:
        if person.first_name[0] not in string.uppercase:
            return QColor('pink')
    
class Admin(Person.Admin):
    field_attributes = {'first_name':{'background_color':first_name_background_color}}

#  ==================================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ==================================================================================
"""Set of classes to store users, groups and permissions"""

import camelot
import camelot.types

from camelot.model import *

__metadata__ = metadata

from camelot.view.elixir_admin import EntityAdmin
import datetime

_current_person_ = None

def getCurrentPerson():
  """Get the currently logged in person"""
  global _current_person_
  if not _current_person_:
    import getpass
    _current_person_ = Person.getOrCreatePerson(getpass.getuser())
  return _current_person_

def updateLastLogin():
  """Update the last login of the current person to now"""
  from elixir import session
  person = getCurrentPerson()
  person.last_login = datetime.datetime.now()
  session.flush([person])
  
class Party(Entity):
  """Base class for persons and organizations.  Use this base class to refer to either persons or
  organisations in building authentication systems, contact management or CRM"""
  using_options(tablename='party')
  
class Person(Party):
  """Person represents natural persons, these can be given access to the system, and
  as such require a username.
  
  Username is required, other fields are optional, there is no password because
  authentication is supposed to happen through the operating system services or other.
  """
  using_options(tablename='person', inheritance='multi')
  username = Field(Unicode(40), required=True, index=True, unique=True)
  first_name = Field(Unicode(40))
  last_name =  Field(Unicode(40))
  middle_name = Field(Unicode(40))
  personal_title = Field(Unicode(10))
  suffix = Field(Unicode(3))
  sex = Field(Unicode(1))
  birthdate = Field(Date())
  martial_status = Field(Unicode(1))
  social_security_number = Field(Unicode(12))
  passport_number = Field(Unicode(20))
  passport_expiry_date = Field(Date())
  is_staff = Field(Boolean, default=False, index=True)
  is_active = Field(Boolean, default=True, index=True)
  is_superuser = Field(Boolean, default=False, index=True)
  last_login = Field(DateTime(), default=datetime.datetime.now)
  date_joined = Field(DateTime(), default=datetime.datetime.now)
  picture = Field(camelot.types.Image(upload_to='person-pictures'), deferred=True)
  comment = Field(Unicode())
  
  def __unicode__(self):
    return self.username
  
  @classmethod
  def getOrCreatePerson(cls, username):
    person = cls.query.filter_by(username=username).first()
    if not person:
      person = cls(username=username)
      from elixir import session
      session.flush([person])
    return person

  class Admin(EntityAdmin):
    name = 'Persons'
    section = 'configuration'
    list_display = ['username', 'first_name', 'last_name', 'last_login']
    fields = ['username', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'last_login', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser']

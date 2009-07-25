#  ============================================================================
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
#  ============================================================================

"""Classes to layout fields on a form.  These are mostly used for specifying the
form_display attribute in Admin classes, but they can be used on their own as
well.  Form classes can be used recursive.
"""

import logging
logger = logging.getLogger('camelot.view.forms')

class Form(object):
  """Base Form class to put fields on a form.  A form can be converted to a
QT widget by calling its render method.  The base form uses the QFormLayout 
to render a form::

  class Admin(EntityAdmin):
    form_display = Form([Label('Please fill this form'), 'title', 'description'])

"""
  
  def __init__(self, content, scrollbars=False):
    """:param content: a list with the field names and forms to render
"""
    assert isinstance(content, list)
    self._content = content
    self._scrollbars = scrollbars
    self._fields = []
    self._add_content(content)

  def _add_content(self, content):
    """add content to the form
    
:param content: a list with field names and forms"""
    for c in content:
      if isinstance(c, Form):
        self._fields.extend(c.get_fields())
      else:
        assert isinstance(c, (str, unicode))
        self._fields.append(c)    
     
  def get_fields(self):
    """:return: the fields, visible in this form"""
    return self._fields
  
  def removeField(self, original_field):
    """Remove a field from the form, This function can be used to modify
inherited forms.

:param original_field: the name of the field to be removed
:return: True if the field was found and removed
    """
    for c in self._content:
      if isinstance(c, Form):
        c.removeField(original_field)
    if original_field in self._content:
      self._content.remove(original_field)
    if original_field in self._fields:
      self._fields.remove(original_field)
      return True
    return False
             
  def replaceField(self, original_field, new_field):
    """Replace a field on this form with another field.  This function can be used to 
modify inherited forms.
    
:param original_field : the name of the field to be replace
:param new_field : the name of the new field
:return: True if the original field was found and replaced.
    
    """
    for i,c in enumerate(self._content):
      if isinstance(c, Form):
        c.replaceField(original_field, new_field)
      elif c==original_field:
        self._content[i] = new_field
    try:
      i = self._fields.index(original_field)
      self._fields[i] = new_field
      return True
    except ValueError:
      pass
    return False
  
  def __unicode__(self):
    return 'Form(%s)'%(u','.join(unicode(c) for c in self._content))
      
  def render(self, widgets, parent=None, nomargins=False):
    """:param widgets: a dictionary mapping each field in this form to a tuple
of (label, widget editor)
 
:return: a QWidget into which the form is rendered
    """
    logger.debug('rendering %s' % self.__class__.__name__) 
    from camelot.view.controls.editors import One2ManyEditor
    from camelot.view.controls.editors import RichTextEditor

    from PyQt4 import QtGui
    from PyQt4.QtCore import Qt

    form_layout = QtGui.QGridLayout()
    row = 0
    for field in self._content:
      if isinstance(field, Form):
        col = 0
        row_span = 1
        col_span = 2
        f = field.render(widgets, parent, True)
        if isinstance(f, QtGui.QLayout):
          form_layout.addLayout(f, row, col, row_span, col_span)
        else:
          form_layout.addWidget(f, row, col, row_span, col_span)
        row += 1
      elif field in widgets:
        col = 0
        row_span = 1
        label, editor = widgets[field]
        if isinstance(editor, (One2ManyEditor, RichTextEditor)):
          col_span = 2
          form_layout.addWidget(label, row, col, row_span, col_span)
          row += 1
          form_layout.addWidget(editor, row, col, row_span, col_span)
          row += 1
        else:
          col_span = 1
          form_layout.addWidget(label, row, col, row_span, col_span)
          #form_layout.addWidget(editor, row, col + 1, row_span, col_span, Qt.AlignRight)
          form_layout.addWidget(editor, row, col + 1, row_span, col_span)
          row += 1

    if self._content:
      # get last item in the layout
      last_item = form_layout.itemAt(form_layout.count() - 1)
  
      # if last item does not contain a widget, 0 is returned
      # which is fine with the isinstance test
      w = last_item.widget()
  
      # add stretch only if last item is not expandable
      if isinstance(w, (One2ManyEditor, RichTextEditor)):
        pass
      else:
        form_layout.setRowStretch(form_layout.rowCount(), 1)

    form_widget = QtGui.QWidget(parent)
    
    # fix embedded forms
    if nomargins:
      form_layout.setContentsMargins(0, 0, 0, 0)

    form_widget.setSizePolicy(QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Expanding)
    form_widget.setLayout(form_layout)
    
    if self._scrollbars:
      scroll_area = QtGui.QScrollArea(parent)
      scroll_area.setWidget(form_widget)
      scroll_area.setWidgetResizable(True)
      scroll_area.setFrameStyle(QtGui.QFrame.NoFrame)
      return scroll_area
 
    return form_widget
  

class Label(Form):
  """Render a label with a QLabel"""

  def __init__(self, label):
    super(Label, self).__init__([])
    self.label = label

  def render(self, widgets, parent=None, nomargins=False):
    from PyQt4 import QtGui
    widget = QtGui.QLabel(self.label)
    return widget

class TabForm(Form):
  """Render forms within a QTabWidget"""
  
  def __init__(self, tabs):
    """:param tabs: a list of tuples of (tab_label, tab_form)"""
    assert isinstance(tabs, list)
    for tab in tabs:
      assert isinstance(tab, tuple)
    self.tabs = [(tab_label,structure_to_form(tab_form)) for tab_label, tab_form in tabs]
    super(TabForm, self).__init__(sum((tab_form.get_fields()
                                  for tab_label, tab_form in self.tabs), []))
    
  def __unicode__(self):
    return 'TabForm { %s\n        }'%(u'\n  '.join('%s : %s'%(label,unicode(form)) for label, form in self.tabs))
  
  def addTab(self, tab_label, tab_form):
    """Add a tab to the form
    
:param tab_label: the name of the tab
:param tab_form: the form to display in the tab or a list of field names.
    """
    tab_form = structure_to_form(tab_form)
    self.tabs.append((tab_label, tab_form))
    self._add_content([tab_form])
                       
  def getTab(self, tab_label):
    """Get the tab form of associated with a tab_label, use this function to
    modify the underlying tab_form in case of inheritance
    
:param tab_label : a label of a tab as passed in the construction method
:return: the tab_form corresponding to tab_label
    """
    for label, form in self.tabs:
      if label==tab_label:
        return form
      
  def replaceField(self, original_field, new_field):
    for tabel, form in self.tabs:
      if form.replaceField(original_field, new_field):
        return True
    return False
    
  def render(self, widgets, parent=None, nomargins=False):
    logger.debug('rendering %s' % self.__class__.__name__) 
    from PyQt4 import QtGui
    from PyQt4.QtCore import Qt
    widget = QtGui.QTabWidget(parent)
    for tab_label, tab_form in self.tabs:      
      widget.addTab(tab_form.render(widgets, widget), tab_label)
    return widget
  

class HBoxForm(Form):
  """Render different forms in a horizontal box"""
  
  def __init__(self, columns):
    """:param columns: a list of forms to display in the different columns
    of the horizontal box"""
    assert isinstance(columns, list)
    self.columns = [structure_to_form(col) for col in columns]
    super(HBoxForm, self).__init__(sum((column_form.get_fields()
                                  for column_form in self.columns), []))

  def __unicode__(self):
    return 'HBoxForm [ %s\n         ]'%('         \n'.join([unicode(form) for form in self.columns])) 
  
  def replaceField(self, original_field, new_field):
    for form in self.columns:
      if form.replaceField(original_field, new_field):
        return True
    return False
  
  def render(self, widgets, parent=None, nomargins=False):
    logger.debug('rendering %s' % self.__class__.__name__) 
    from PyQt4 import QtGui
    form_layout = QtGui.QHBoxLayout()
    for form in self.columns:
      f = form.render(widgets, parent, nomargins)
      if isinstance(f, QtGui.QLayout):
        form_layout.addLayout(f)
      else:
        form_layout.addWidget(f)
    return form_layout

class VBoxForm(Form):
  """Render different forms or widgets in a vertical box"""
  
  def __init__(self, rows):
    """:param rows: a list of forms to display in the different columns
    of the horizontal box
    """
    assert isinstance(rows, list)
    self.rows = [structure_to_form(row) for row in rows]
    super(VBoxForm, self).__init__(sum((row_form.get_fields() for row_form in self.rows), []))

  def replaceField(self, original_field, new_field):
    for form in self.rows:
      if form.replaceField(original_field, new_field):
        return True
    return False
  
  def __unicode__(self):
    return 'VBoxForm [ %s\n         ]'%('         \n'.join([unicode(form) for form in self.rows]))
  
  def render(self, widgets, parent=None, nomargins=False):
    logger.debug('rendering %s' % self.__class__.__name__) 
    from PyQt4 import QtGui
    form_layout = QtGui.QVBoxLayout()
    for form in self.rows:
      f = form.render(widgets, parent, nomargins)
      if isinstance(f, QtGui.QLayout):
        form_layout.addLayout(f)
      else:
        form_layout.addWidget(f)
    return form_layout
  
class GridForm(Form):
  """Put different fields into a grid::

  GridForm([['A1', 'B1'], ['A2','B2']])
  
"""
  
  def __init__(self, grid):
    """:param grid: A list for each row in the grid, containing a list with all fields that should be put in that row
    """
    assert isinstance(grid, list)
    self._grid = grid
    fields = []
    for row in grid:
      assert isinstance(row, list)
      fields.extend(row)
    super(GridForm, self).__init__(fields)

  def render(self, widgets, parent=None, nomargins=False):
    from PyQt4 import QtGui
    widget = QtGui.QWidget(parent)
    grid_layout = QtGui.QGridLayout()
    for i,row in enumerate(self._grid):
      for j,field in enumerate(row):
        if isinstance(field, Form):
          grid_layout.addWidget(field.render([], grid_layout), i, j)
        else:
          label, editor = widgets[field]
          grid_layout.addWidget(editor, i, j)
    widget.setLayout(grid_layout)
    return widget

class WidgetOnlyForm(Form):
  """Renders a single widget without its label, typically a one2many widget"""
  
  def __init__(self, field):
    assert isinstance(field, (str, unicode))
    super(WidgetOnlyForm, self).__init__([field])
    
  def render(self, widgets, parent=None, nomargins=False):
    logger.debug('rendering %s' % self.__class__.__name__) 
    label, editor = widgets[self.get_fields()[0]]
    return editor
  
class GroupBoxForm(Form):
  """
Renders a form within a QGroupBox::
  
  class Admin(EntityAdmin):
    form_display = ['title', GroupBoxForm('Ratings', ['expert_rating', 'public_rating'])]
  
  """
  
  def __init__(self, title, content):
    self.title = title
    Form.__init__(self, content)

  def render(self, widgets, parent=None, nomargins=False):
    from PyQt4 import QtGui
    widget = QtGui.QGroupBox(self.title, parent)
    layout = QtGui.QVBoxLayout()
    widget.setLayout(layout)
    form = Form.render(self, widgets, widget, nomargins)
    layout.addWidget(form)
    return widget

def structure_to_form(structure):
  """Convert a python data structure to a form, using the following rules :
  
 * if structure is an instance of Form, return structure
 * if structure is a list, create a Form from this list
  
This function is mainly used in the Admin class to construct forms out of
the form_display attribute   
  """
  if isinstance(structure, Form):
    return structure
  return Form(structure)

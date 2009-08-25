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

"""form view"""

import logging
logger = logging.getLogger('camelot.view.controls.formview')

from PyQt4 import QtCore
from PyQt4 import QtGui
from camelot.view.model_thread import model_function
from camelot.view.controls.view import AbstractView

class FormView(QtGui.QWidget, AbstractView):
  def __init__(self, title, admin, model, index):
    QtGui.QWidget.__init__(self)
    self.title_prefix = title
    self.admin = admin
    self.model = model
    self.index = index
    self.setWindowTitle(title)
    self.widget_mapper = QtGui.QDataWidgetMapper()
    self.widget_layout = QtGui.QHBoxLayout()

    self.closeAfterValidation = QtCore.SIGNAL('closeAfterValidation()')
    sig = 'dataChanged(const QModelIndex &, const QModelIndex &)'
    self.connect(self.model, QtCore.SIGNAL(sig), self.dataChanged)

    self.widget_mapper.setModel(model)
    self.setLayout(self.widget_layout)

    if hasattr(admin, 'form_size') and admin.form_size:
      self.setMinimumSize(admin.form_size[0], admin.form_size[1])

    self.validator = admin.createValidator(model)
    self.validate_before_close = True

    def getColumnsAndForm():
      return (self.model.getColumns(), self.admin.getForm())

    self.admin.mt.post(getColumnsAndForm, 
                       lambda (columns, form):
                       self.handleGetColumnsAndForm(columns, form))

    def getActions():
      return admin.get_form_actions(None)

    self.admin.mt.post(getActions, self.setActions)
    self.update_title()
    
  def update_title(self):
    
    def get_title():
      obj = self.getEntity()
      return u'%s %s'%(self.title_prefix, self.admin.get_verbose_identifier(obj))
    
    def set_title(title):
      import sip
      if not sip.isdeleted(self):
        self.setWindowTitle(title)
    
    self.admin.mt.post(get_title, set_title)

  def dataChanged(self, index_from, index_to):
    #@TODO: only revert if this form is in the changed range
    self.widget_mapper.revert()
    self.update_title()

  def handleGetColumnsAndForm(self, columns, form):
    import sip
    if not sip.isdeleted(self):
      delegate = self.model.getItemDelegate()
      self.setColumnsFormAndDelegate(columns, form, delegate)

  def setColumnsFormAndDelegate(self, columns, form, delegate):
    """Create value and label widgets"""
    widgets = {}
    self.widget_mapper.setItemDelegate(delegate)
    
    for i, (field_name, field_attributes) in enumerate(columns):
      option = None
      model_index = self.model.index(self.index, i)
      widget_label = QtGui.QLabel(field_attributes['name'])
      widget_editor = delegate.createEditor(None, option, model_index)

      # required fields font is bold
      if ('nullable' in field_attributes) and \
         (not field_attributes['nullable']):
        font = QtGui.QApplication.font()
        font.setBold(True)
        widget_label.setFont(font)

      self.widget_mapper.addMapping(widget_editor, i)
      widgets[field_name] = (widget_label, widget_editor)
      
    self.widget_mapper.setCurrentIndex(self.index)
    self.widget_layout.insertWidget(0, form.render(widgets, self))
    self.widget_layout.setContentsMargins(7, 7, 7, 7)        

  def getEntity(self):
    return self.model._get_object(self.widget_mapper.currentIndex())

  def setActions(self, actions):
    import sip
    if not sip.isdeleted(self) and actions:
      from actionsbox import ActionsBox
      logger.debug('setting Actions for formview')
      self.actions_widget = ActionsBox(self, self.getEntity)
      self.actions_widget.setActions(actions)
      self.widget_layout.insertWidget(1, self.actions_widget)

  def viewFirst(self):
    """select model's first row"""
    # submit should not happen a second time, since then we don't want
    # the widgets data to be written to the model
    self.widget_mapper.submit()        
    self.widget_mapper.toFirst()
    self.update_title()

  def viewLast(self):
    """select model's last row"""
    # submit should not happen a second time, since then we don't want
    # the widgets data to be written to the model
    self.widget_mapper.submit()         
    self.widget_mapper.toLast()
    self.update_title()

  def viewNext(self):
    """select model's next row"""
    # submit should not happen a second time, since then we don't want
    # the widgets data to be written to the model
    self.widget_mapper.submit()         
    self.widget_mapper.toNext()
    self.update_title()

  def viewPrevious(self):
    """select model's previous row"""
    # submit should not happen a second time, since then we don't want
    # the widgets data to be written to the model
    self.widget_mapper.submit()         
    self.widget_mapper.toPrevious()
    self.update_title()            

  def validateClose(self):
    logger.debug('validate before close : %s' % self.validate_before_close)
    if self.validate_before_close:
      # submit should not happen a second time, since then we don't
      # want the widgets data to be written to the model
      self.widget_mapper.submit()
      
      def validate():
        return self.validator.isValid(self.widget_mapper.currentIndex())
                          
      def showMessage(valid):
        import sip
        if not valid:
          reply = self.validator.validityDialog(self.widget_mapper.currentIndex(), self).exec_()
          if reply == QtGui.QMessageBox.Discard:
            # clear mapping to prevent data being written again to the model,
            # then we reverted the row
            self.widget_mapper.clearMapping()
            self.model.revertRow(self.widget_mapper.currentIndex())
            self.validate_before_close = False
            self.emit(self.closeAfterValidation)
        else:
          self.validate_before_close = False
          if not sip.isdeleted(self):
            self.emit(self.closeAfterValidation)
      
      self.admin.mt.post(validate, showMessage)
      return False

    return True

  def closeEvent(self, event):
    logger.debug('formview closed')
    if self.validateClose():
      event.accept()
    else:
      event.ignore()

  @model_function
  def toHtml(self):
    """generates html of the form"""

    import settings
    from jinja import Environment
    from jinja import FileSystemLoader

    def to_html(d=u''):
      """Jinja 1 filter to convert field values to their default html
      representation
      """
      
      def wrapped_in_table(env, context, value):
        if isinstance(value, list):
          return u'<table><tr><td>' +\
                 u'</td></tr><tr><td>'.join([unicode(e) for e in value]) +\
                 u'</td></tr></table>'
        return unicode(value)
      
      return wrapped_in_table

    entity = self.getEntity()
    fields = self.admin.getFields()
    table = [dict(field_attributes = field_attributes,
                  value = getattr(entity, name))
                  for name, field_attributes in fields]

    context = {
      'title': self.admin.get_verbose_name(),
      'table': table,
    }

    from camelot.view.templates import loader
    env = Environment(loader=loader)
    env.filters['to_html'] = to_html        
    tp = env.get_template('form_view.html')

    return tp.render(context)

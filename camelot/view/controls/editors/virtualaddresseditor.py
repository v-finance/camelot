
from customeditor import *
from camelot.view.art import Icon

class VirtualAddressEditor(CustomEditor):
  
  def __init__(self, parent=None, editable=True):
    CustomEditor.__init__(self, parent)
    self.layout = QtGui.QHBoxLayout()
    self.layout.setMargin(0)
    self.combo = QtGui.QComboBox()
    self.combo.addItems(camelot.types.VirtualAddress.virtual_address_types)
    self.layout.addWidget(self.combo)
    self.editor = QtGui.QLineEdit()
    self.layout.addWidget(self.editor)
#    if virtual_adress[0] == 'email':
#      icon = Icon('tango/16x16/apps/internet-mail.png').getQPixmap()
#    else:
#      #if virtual_adress[0] == 'telephone':
    icon = Icon('tango/16x16/actions/zero.png').getQPixmap()
#      
    self.label = QtGui.QLabel()
    self.label.setPixmap(icon)
    
    self.connect(self.editor,
                 QtCore.SIGNAL('editingFinished()'),
                 self.editingFinished)
    self.connect(self.editor,
                 QtCore.SIGNAL('textEdited(const QString&)'),
                 self.editorValueChanged)
    self.connect(self.combo,
                 QtCore.SIGNAL('currentIndexChanged(int)'),
                 lambda:self.comboIndexChanged())
    self.setLayout(self.layout)
    self.setAutoFillBackground(True)

  def comboIndexChanged(self):
    self.checkValue(self.editor.text())
    self.editingFinished()
    
  def set_value(self, value):
    value = CustomEditor.set_value(self, value)
    if value:
      self.editor.setText(value[1])
      idx = camelot.types.VirtualAddress.virtual_address_types.index(value[0])
      self.combo.setCurrentIndex(idx)
      if str(self.combo.currentText()) == 'phone':
        icon = Icon('tango/16x16/devices/phone.png').getQPixmap()
      if str(self.combo.currentText()) == 'fax':
        icon = Icon('tango/16x16/devices/printer.png').getQPixmap()
      if str(self.combo.currentText()) == 'mobile':
        icon = Icon('tango/16x16/devices/mobile.png').getQPixmap()
      if str(self.combo.currentText()) == 'im':
        icon = Icon('tango/16x16/places/instant-messaging.png').getQPixmap()
      if str(self.combo.currentText()) == 'pager':
        icon = Icon('tango/16x16/devices/pager.png').getQPixmap()
        
      if str(self.combo.currentText()) == 'email':
        icon = Icon('tango/16x16/apps/internet-mail.png').getQIcon()
        self.label.deleteLater()
        self.label = QtGui.QToolButton()
        self.label.setFocusPolicy(Qt.StrongFocus)
        self.label.setAutoRaise(True)
        self.label.setAutoFillBackground(True)
        self.label.setIcon(icon)
        self.connect(self.label,
                     QtCore.SIGNAL('clicked()'),
                     lambda:self.mailClick(self.editor.text()))
      else:
        self.label.deleteLater()
        self.label = QtGui.QLabel()
        self.label.setPixmap(icon)

      self.layout.addWidget(self.label)

  def get_value(self):
    value = (unicode(self.combo.currentText()), unicode(self.editor.text()))
    return CustomEditor.get_value(self) or value

  def checkValue(self, text):
    if self.combo.currentText() == 'email':
      email = unicode(text)
      mailCheck = re.compile('^\S+@\S+\.\S+$')
      if not mailCheck.match(email):
        palette = self.editor.palette()
        palette.setColor(QtGui.QPalette.Active,
                         QtGui.QPalette.Base,
                         QtGui.QColor(255, 0, 0))
        self.editor.setPalette(palette)
      else:
        palette = self.editor.palette()
        palette.setColor(QtGui.QPalette.Active,
                         QtGui.QPalette.Base,
                         QtGui.QColor(255, 255, 255))
        self.editor.setPalette(palette)
        
    elif self.combo.currentText() == 'phone' \
     or self.combo.currentText() == 'pager' \
     or self.combo.currentText() == 'fax' \
     or self.combo.currentText() == 'mobile':

      number = text
      numberCheck = re.compile('^[0-9 ]*$')

      if not numberCheck.match(number):
        palette = self.editor.palette()
        palette.setColor(QtGui.QPalette.Active,
                         QtGui.QPalette.Base,
                         QtGui.QColor(255, 0, 0))
        self.editor.setPalette(palette)
      else:
        palette = self.editor.palette()
        palette.setColor(QtGui.QPalette.Active,
                         QtGui.QPalette.Base,
                         QtGui.QColor(255, 255, 255))
        self.editor.setPalette(palette)

  def editorValueChanged(self, text):
    self.checkValue(text)

  def mailClick(self, adress):
    url = QtCore.QUrl()
    url.setUrl('mailto:'+str(adress)+'?subject=Camelot')
    mailSent = QtGui.QDesktopServices.openUrl(url)
    if not mailSent:
      print 'Failed to send Mail.'
    else:
      print 'mail client opened.'

  def editingFinished(self):
    self.value = []
    self.value.append(str(self.combo.currentText()))
    self.value.append(str(self.editor.text()))
    self.set_value(self.value)
    self.label.setFocus()
    self.emit(QtCore.SIGNAL('editingFinished()'))


import os
import tempfile

from customeditor import *
from camelot.view.art import Icon

try:
  from PIL import Image as PILImage
except:
  import Image as PILImage

filter = """Image files (*.bmp *.jpg *.jpeg *.mng *.png *.pbm *.pgm *.ppm *.tiff *.xbm *.xpm)
All files (*)"""

class ImageEditor(CustomEditor):
    
  def __init__(self, parent=None, editable=True, **kwargs):
    CustomEditor.__init__(self, parent)
    
    self.clear_icon = Icon('tango/16x16/actions/edit-delete.png').getQIcon()
    self.new_icon = Icon('tango/16x16/actions/list-add.png').getQIcon()
    self.open_icon = Icon('tango/16x16/actions/document-open.png').getQIcon()
    self.saveas_icon = Icon('tango/16x16/actions/document-save-as.png').getQIcon()
  
    self._modified = False
    self.image = None 
    self.layout = QtGui.QHBoxLayout()
    #
    # Setup label
    #
    self.label = QtGui.QLabel(parent)
    self.label.setEnabled(editable)
    self.layout.addWidget(self.label)
    self.label.setAcceptDrops(True)
    # self.draw_border()
    self.label.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
    self.label.__class__.dragEnterEvent = self.dragEnterEvent
    self.label.__class__.dragMoveEvent = self.dragEnterEvent
    self.label.__class__.dropEvent = self.dropEvent
    #
    # Setup buttons
    #
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    button_layout.setMargin(0)

    file_button = QtGui.QToolButton()
    file_button.setIcon(self.new_icon)
    file_button.setEnabled(editable)
    file_button.setAutoRaise(True)
    file_button.setToolTip('Select image')
    self.connect(file_button, QtCore.SIGNAL('clicked()'), self.openFileDialog)
    
    app_button = QtGui.QToolButton()
    app_button.setIcon(self.open_icon)
    app_button.setEnabled(editable)
    app_button.setAutoRaise(True)
    app_button.setToolTip('Open image')
    self.connect(app_button, QtCore.SIGNAL('clicked()'), self.openInApp)
    
    clear_button = QtGui.QToolButton()
    clear_button.setIcon(self.clear_icon)
    clear_button.setEnabled(editable)
    clear_button.setToolTip('Delete image')
    clear_button.setAutoRaise(True)
    self.connect(clear_button, QtCore.SIGNAL('clicked()'), self.clearImage)

    vspacerItem = QtGui.QSpacerItem(20,
                                    20,
                                    QtGui.QSizePolicy.Minimum,
                                    QtGui.QSizePolicy.Expanding)
    
    button_layout.addItem(vspacerItem)
    button_layout.addWidget(file_button)      
    button_layout.addWidget(app_button)
    button_layout.addWidget(clear_button)    

    self.layout.addLayout(button_layout)
    
    hspacerItem = QtGui.QSpacerItem(20,
                                    20,
                                    QtGui.QSizePolicy.Expanding,
                                    QtGui.QSizePolicy.Minimum)
    self.layout.addItem(hspacerItem)
    self.setLayout(self.layout)
    #
    # Image
    #
    self.dummy_image = Icon('tango/32x32/apps/help-browser.png').fullpath()
    if self.image is None:
      testImage = QtGui.QImage(self.dummy_image)
      if not testImage.isNull():
        fp = open(self.dummy_image, 'rb')
        self.image = PILImage.open(fp)
        self.setPixmap(QtGui.QPixmap(self.dummy_image))

  def set_value(self, value):
    import StringIO
    data = CustomEditor.set_value(self, value)
    if data:
      s = StringIO.StringIO()
      self.image = data.image
      data = data.image.copy()
      data.thumbnail((100, 100))
      data.save(s, 'png')
      s.seek(0)
      pixmap = QtGui.QPixmap()
      pixmap.loadFromData(s.read())
      s.close()
      self.setPixmap(pixmap)
      self.setModified(False)
    else:
      self.clearFirstImage()
          
  def isModified(self):
    return self._modified
  
  def set_enabled(self, editable=True):
    self.__init__(None, editable)

  def setModified(self, modified):
    self._modified = modified

  #
  # Drag & Drop
  #
  def dragEnterEvent(self, event):
    event.acceptProposedAction()

  def dragMoveEvent(self, event):
    event.acceptProposedAction()

  def dropEvent(self, event):
    if event.mimeData().hasUrls():
      url = event.mimeData().urls()[0]
      filename = url.toLocalFile()
      if filename != '':
        self.pilimage_from_file(filename)

  #
  # Buttons methods
  #
  def clearImage(self):
    self.pilimage_from_file(self.dummy_image)
    self.draw_border()

  def openFileDialog(self):
    filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                                                 QtCore.QDir.currentPath(),
                                                 filter)
    if filename != '':
      self.pilimage_from_file(filename)

  def openInApp(self):
    if self.image != None:
      tmpfp, tmpfile = tempfile.mkstemp(suffix='.png')
      self.image.save(os.fdopen(tmpfp, 'wb'), 'png')
      QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(tmpfile))

  #
  # Utils methods
  #
  def pilimage_from_file(self, filepath):
    testImage = QtGui.QImage(filepath)
    if not testImage.isNull():
      fp = open(filepath, 'rb')
      self.image = PILImage.open(fp)
      self._modified = True
      self.emit(QtCore.SIGNAL('editingFinished()'))
  
  def draw_border(self):
    self.label.setFrameShape(QtGui.QFrame.Box)
    self.label.setFrameShadow(QtGui.QFrame.Plain)
    self.label.setLineWidth(1)
    self.label.setFixedSize(100, 100)
   
  def setPixmap(self, pixmap):
    self.label.setPixmap(pixmap)      
    self.draw_border()

  def clearFirstImage(self):
    testImage = QtGui.QImage(self.dummy_image)
    if not testImage.isNull():
      fp = open(self.dummy_image, 'rb')
      self.image = PILImage.open(fp)
    self.draw_border()

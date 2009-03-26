import sys
import urllib
from camelot.view.model_thread import get_model_thread
from camelot.view.workspace import get_workspace
from camelot.view.controls.exception import model_thread_exception_message_box
from camelot.view import art
from camelot.view.elixir_admin import EntityAdmin
from xml.etree.ElementTree import fromstring
from PyQt4 import QtGui, QtCore

#def run_wizard(arg):
#  ws = get_workspace()
#  wizard = ConfigurationWizard(ws)
#  wizard.setPixmap(QtGui.QWizard.LogoPixmap, QtGui.QPixmap(Icon('tango/24x24/emotes/smile.png').getQPixmap()))  
#  wizard.show()
#  wizard.exec_()
#  
#def configure():
#  mt = get_model_thread()
#  mt.post(lambda:None, run_wizard)
  


class NewCompanyWizard(QtGui.QWizard):
  
  
  
  
  def __init__(admin, o, parent=None):
    
    super(NewCompanyWizard, admin).__init__(parent)
    admin.value = ''
    o.name = ''
    admin.setWindowTitle('New Company Wizard')
    combobox = QtGui.QComboBox()
    combobox.insertItem(0, unicode('Loading list ...'), QtCore.QVariant(all))

    
    
    
    class WelcomePage(QtGui.QWizardPage):
      def __init__(self):
        super(WelcomePage, self).__init__()
        self.setTitle('New Company Wizard')
        self.setSubTitle('Welcome, This wizard will help you to add a new company')

        
    class inputPage(QtGui.QWizardPage):
      
      def __init__(self):
        super(inputPage, self).__init__() 
        self.comboBox = QtGui.QComboBox()
        self.vat = QtGui.QLineEdit()     
        self.setTitle('New Company Wizard')
        self.setSubTitle('Select the company\'s country, and fill in its VAT Number')
        layout = QtGui.QHBoxLayout()
        layout.addSpacing(30)
        layout.addWidget(self.comboBox)
        layout.addWidget(self.vat)
        #layout.maximumSize()
        self.connect(self.vat, QtCore.SIGNAL('textChanged(const QString&)'), self.textChanged)
        
        layout.addStretch(0)
        self.setLayout(layout)
        
      def textChanged(self, text):
        #print 'textChanged'
        self.emit(QtCore.SIGNAL('completeChanged()'))

      def isComplete(self):
        admin.value = str(self.comboBox.currentText())[0:2] + str(self.vat.text())
        
        #print admin.value[11:]

        if admin.value[10:] is '':
          return False
        else:
          return True
      
      def initializePage(self):
        
        landen = QtCore.QStringList()
        landen.append('AT - Austria')
        landen.append('BE - Belgium')
        landen.append('BG - Bulgaria')
        landen.append('CY - Cyprus')
        landen.append('CZ - Czech Republic')
        landen.append('DE - Germany')
        landen.append('DK - Denmark')
        landen.append('EE - Estonia')
        landen.append('EL - Greece ')
        landen.append('ES - Spain ')
        landen.append('FI - Finland')
        landen.append('FR - France')
        landen.append('GB - United Kingdom')
        landen.append('HU - Hungary')
        landen.append('IE - Ireland')
        landen.append('IT - Italy')
        landen.append('LT - Lithuania')
        landen.append('LU - Luxembourg')
        landen.append('LV - Latvia')
        landen.append('MT - Malta')
        landen.append('NL - The Netherlands')
        landen.append('PL - Poland')
        landen.append('PT - Portugal')
        landen.append('RO - Romania')
        landen.append('SE - Sweden')
        landen.append('SI - Slovenia')
        landen.append('sK - Slovakia')
        
        self.comboBox.addItems(landen)
        
                  
    class checkPage(QtGui.QWizardPage):
      def __init__(self):
        super(checkPage, self).__init__()
        
        self.succes = False
        self.ondernemingsVorm = QtGui.QLabel()
        self.name = QtGui.QLabel()
        self.street = QtGui.QLabel()
        self.town = QtGui.QLabel()
        
        

        
              
        self.setTitle('Add New Company')
        if self.succes == False:
          self.setSubTitle('')
        else:
          self.setSubTitle('Here is the adress we found in the database, make sure this is correct.')
          
        layout = QtGui.QVBoxLayout()
        
        naamlayout = QtGui.QHBoxLayout()
        naamlayout.addWidget(self.ondernemingsVorm)
        naamlayout.addWidget(self.name)
  
        layout.addLayout(naamlayout)
        layout.addWidget(self.street)
        layout.addWidget(self.town)
        layout.addStretch(1)
        self.setLayout(layout)
        


      def isComplete(self):
        if not self.succes:
          return False
        else:
          return True
        
                
      def initializePage(self):
        url = 'http://ec.europa.eu/taxation_customs/vies/viesquer.do?ms=' + admin.value[0:2] + '&iso=' + admin.value[0:2] + '&vat=' + admin.value[2:]

        
        
        
        
        file = urllib.urlopen(url)

        test = file.readlines()
        
#        for i, line in enumerate(test):
#          print i, line
          
        
        
          
        succes = str(test[323])
        name = str(test[365])
        adress = str(test[378])
        
        
        succes = succes.strip()
        
        if succes[0] == 'S':
          self.setSubTitle('System Overloaded, please try again later.')
        else:
        
          if succes[0] == 'Y':
            self.succes = True
          else:
            self.succes = False
            
            
            
          if self.succes == False:
            self.setSubTitle('')
          else:
            self.setSubTitle('Here is the adress we found in the database, make sure this is correct.')
            
            name = name.strip()
            
            
    
            if name.find(' ') == -1:
              print 'HOPLA!'
              self.setSubTitle('VAT Number Correct, but no information was found in the Database.')
              self.name.setText('')
              self.ondernemingsVorm.setText('')
              self.street.setText('')
              self.town.setText('')
            else:
              self.name.setText(name)
              
              firstSpace = name.index(' ')
            
              self.ondernemingsVorm.setText(name[0:firstSpace])
            
              name = name[firstSpace:]
            
              name = name.strip()
            
              self.name.setText(name)
              
              adress = adress.strip()
              
              firstTag = adress.index('<')
              
              street = adress[0:firstTag]
              
              adress = adress[firstTag+4:]
              
              town = adress
              
              #adress = town + ' ' + street
              
              self.street.setText(street)
              self.town.setText(town)
              
              
              taxid = str(admin.value)

              from camelot.view.model_thread import get_model_thread
              mt = get_model_thread()
              
              def set_model_data():
                o.name = name
                o.taxid = taxid
                print o.name
                print o.taxid
  
              mt.post(set_model_data)
              
          
          if not self.succes:
            self.ondernemingsVorm.setText('Nothing Found.')
            self.name.setText(' ')
            self.street.setText('Please retyp the VAT number')
            self.town.setText(' ')
        
        
        
        
          
    
    
    admin.addPage(WelcomePage())
    admin.addPage(inputPage())
    admin.addPage(checkPage())
    
    
#app = QtGui.QApplication(sys.argv)
#wiz = NewCompanyWizard()
#wiz.show()
#wiz.exec_()
    
    
#import urllib
#from PyQt4 import QtGui, QtCore
#
#class NewCompanyWizard( QtGui.QWizard ):
#    def __init__( wizard, organization_getter, parent = None ):
#        super( NewCompanyWizard, wizard ).__init__( parent )
#        wizard.value = ''
#        wizard.success = False
#        wizard.name = ''
#        wizard.town = ''
#        wizard.street = ''
#        wizard.taxid = ''
#        wizard.setWindowTitle( 'New Company Wizard' )
#        combobox = QtGui.QComboBox()
#        combobox.insertItem( 0, unicode( 'Loading list ...' ), QtCore.QVariant( all ) )
#
#        class WelcomePage( QtGui.QWizardPage ):
#            def __init__( self ):
#                super( WelcomePage, self ).__init__()
#                self.setTitle( 'New Company Wizard' )
#                self.setSubTitle( 'Welcome, This wizard will help you to add a new company' )
#
#        class inputPage( QtGui.QWizardPage ):
#            def __init__( self ):
#                super( inputPage, self ).__init__()
#                self.comboBox = QtGui.QComboBox()
#                self.vat = QtGui.QLineEdit()
#                self.setTitle( 'New Company Wizard' )
#                self.setSubTitle( 'Select the company\'s country, and fill in its VAT Number' )
#                layout = QtGui.QHBoxLayout()
#                layout.addSpacing( 30 )
#                layout.addWidget( self.comboBox )
#                layout.addWidget( self.vat )
#                #layout.maximumSize()
#                self.connect( self.vat, QtCore.SIGNAL( 'textChanged(const QString&)' ), self.textChanged )
#                layout.addStretch( 0 )
#                self.setLayout( layout )
#
#            def textChanged( self, text ):
#                self.emit( QtCore.SIGNAL( 'completeChanged()' ) )
#
#            def isComplete( self ):
#                wizard.value = str( self.comboBox.currentText() )[0:2] + str( self.vat.text() )
#                if wizard.value[10:] is '':
#                    return False
#                else:
#                    return True
#
#            def initializePage( self ):
#                landen = QtCore.QStringList()
#                landen.append( 'AT - Austria' )
#                landen.append( 'BE - Belgium' )
#                landen.append( 'BG - Bulgaria' )
#                landen.append( 'CY - Cyprus' )
#                landen.append( 'CZ - Czech Republic' )
#                landen.append( 'DE - Germany' )
#                landen.append( 'DK - Denmark' )
#                landen.append( 'EE - Estonia' )
#                landen.append( 'EL - Greece ' )
#                landen.append( 'ES - Spain ' )
#                landen.append( 'FI - Finland' )
#                landen.append( 'FR - France' )
#                landen.append( 'GB - United Kingdom' )
#                landen.append( 'HU - Hungary' )
#                landen.append( 'IE - Ireland' )
#                landen.append( 'IT - Italy' )
#                landen.append( 'LT - Lithuania' )
#                landen.append( 'LU - Luxembourg' )
#                landen.append( 'LV - Latvia' )
#                landen.append( 'MT - Malta' )
#                landen.append( 'NL - The Netherlands' )
#                landen.append( 'PL - Poland' )
#                landen.append( 'PT - Portugal' )
#                landen.append( 'RO - Romania' )
#                landen.append( 'SE - Sweden' )
#                landen.append( 'SI - Slovenia' )
#                landen.append( 'sK - Slovakia' )
#                self.comboBox.addItems( landen )
#
#        class checkPage( QtGui.QWizardPage ):
#            def __init__( self ):
#                super( checkPage, self ).__init__()
#                self.success = False
#                self.ondernemingsVorm = QtGui.QLabel()
#                self.name = QtGui.QLabel()
#                self.street = QtGui.QLabel()
#                self.town = QtGui.QLabel()
#                self.setTitle( 'Add New Company' )
#                if self.success == False:
#                    self.setSubTitle( '' )
#                else:
#                    self.setSubTitle( 'Here is the adress we found in the database, make sure this is correct.' )
#                layout = QtGui.QVBoxLayout()
#                naamlayout = QtGui.QHBoxLayout()
#                naamlayout.addWidget( self.ondernemingsVorm )
#                naamlayout.addWidget( self.name )
#                layout.addLayout( naamlayout )
#                layout.addWidget( self.street )
#                layout.addWidget( self.town )
#                layout.addStretch( 1 )
#                self.setLayout( layout )
#
#            def isComplete( self ):
#                if not wizard.success:
#                    return False
#                else:
#                    return True
#
#            def initializePage( self ):
#                url = 'http://ec.europa.eu/taxation_customs/vies/viesquer.do?ms=' + wizard.value[0:2] + '&iso=' + wizard.value[0:2] + '&vat=' + wizard.value[2:]
#                file = urllib.urlopen( url )
#                test = file.readlines()
#                succes = str( test[323] )
#                name = str( test[365] )
#                adress = str( test[378] )
#                succes = succes.strip()
#                print succes
#                if succes[0] == 'S':
#                    self.setSubTitle( 'System Overloaded, please try again later.' )
#                else:
#                    if succes[0] == 'Y':
#                        wizard.success = True
#                    else:
#                        wizard.success = False
#                    if wizard.success == False:
#                        self.setSubTitle( '' )
#                    else:
#                        self.setSubTitle( 'Here is the address we found in the database, make sure this is correct.' )
#                        name = name.strip()
#                        if name.find( ' ' ) == -1:
#                            self.setSubTitle( 'VAT Number Correct, but no information was found in the Database.' )
#                            self.name.setText( '' )
#                            self.ondernemingsVorm.setText( '' )
#                            self.street.setText( '' )
#                            self.town.setText( '' )
#                        else:
#                            self.name.setText( name )
#                            firstSpace = name.index( ' ' )
#                            self.ondernemingsVorm.setText( name[0:firstSpace] )
#                            name = name[firstSpace:]
#                            wizard.name = name.strip()
#                            self.name.setText( name )
#                            adress = adress.strip()
#                            firstTag = adress.index( '<' )
#                            wizard.street = adress[0:firstTag]
#                            adress = adress[firstTag + 4:]
#                            wizard.town = adress
#                            self.street.setText( wizard.street )
#                            self.town.setText( wizard.town )
#                            wizard.taxid = str( wizard.value )
#                    if not wizard.success:
#                        self.ondernemingsVorm.setText( 'Nothing Found.' )
#                        self.name.setText( ' ' )
#                        self.street.setText( 'Please retyp the VAT number' )
#                        self.town.setText( ' ' )
#
#        wizard.addPage( WelcomePage() )
#        wizard.addPage( inputPage() )
#        wizard.addPage( checkPage() )
#
#    def finished( self, result ):
#        pass

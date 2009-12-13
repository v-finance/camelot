from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QWizard, QWizardPage, QToolBar, QFileDialog, QPushButton, QTableView, QFont, QVBoxLayout, QGridLayout, QLabel, QComboBox, QItemDelegate, QStandardItemModel, QColor, QCheckBox
from PyQt4.QtCore import QString, QAbstractTableModel, QVariant, Qt, QAbstractListModel, QModelIndex, QStringList, QPoint
from camelot.view import art
from camelot.view.art import Icon
from camelot.action import createAction, addActions
from camelot.view.elixir_admin import EntityAdmin
from camelot.view.model_thread import get_model_thread
from camelot.view.controls.exception import model_thread_exception_message_box
from camelot.view.controls.delegates.comboboxdelegate import ComboBoxEditorDelegate, TestComboBoxDelegate
from camelot.view.controls.editors.choiceseditor import ChoicesEditor
import csv, itertools

_ = lambda x: x

class ImportWizard(QtGui.QWizard):
    """Import wizard GUI"""
    def __init__(self, parent, attributes):
        QWizard.__init__(self)
        self.parent = parent
        # the attributes of the object that will be imported
        self.attributes = attributes

    """ Make a wizard and the pages """
    def start(self):
        self.qWizard = QWizard()
        self.qWizard.setEnabled(True)
        # qPage is the introduction page
        self.qPage = ImportWizardPage(self.qWizard)
        self.qPage.setTitle(QString('import wizard'))

        self.makeToolBarToSearchFile()

        #make grid
        self.makeGridLayout()

        #add layout to page
        self.qPage.setLayout(self.grid)
        self.qWizard.addPage(self.qPage)

        #make the page that shows the table
        self.qTablePage = QWizardPage(self.qWizard)
        self.qTablePage.setTitle(QString('Data from file'))

        self.qWizard.addPage(self.qTablePage)

        cancelButton = QPushButton(QString('cancel'), self.qWizard)
        self.qWizard.setButton(QWizard.CancelButton, cancelButton)

        finishButton = QWizard.FinishButton
        self.qWizard.setButtonText(finishButton, QString('import'))

        self.qWizard.show()
        self.qWizard.exec_()

    """
        makes toolbar with button to open a csv-file. this is added at the qpage of a qwizard
    """
    def makeToolBarToSearchFile(self):
        self.openToolBar = QToolBar(self.qPage)
        icon_file_open = Icon('tango/32x32/actions/fileopen.png').fullpath()
        openAct = QtGui.QAction(QtGui.QIcon(icon_file_open), 'Open File', self.openToolBar)
        self.openToolBar.connect(openAct, QtCore.SIGNAL('triggered()'), self.showOpenFileDialog)
        self.openToolBar.addAction(openAct)

    def makeCheckBoxForFirstRow(self):
        self.checkBox = QCheckBox('first row of data is column name')
        action = QtGui.QAction('CheckBox', self.checkBox)
        self.checkBox.connect(self.checkBox, QtCore.SIGNAL("clicked()"), self.repaintTable)
        self.checkBox.addAction(action)
    
        checkBox = QCheckBox('first row of data is column name')
        action = QtGui.QAction('CheckBox', checkBox)
        checkBox.connect(action, QtCore.SIGNAL('clicked()'), self.repaintTable)
        checkBox.addAction(action)
        return checkBox

    """
        depending on the checkbox the table must be drawn again
    """
    def repaintTable(self):
        print 'repaint table'
        if self.checkBox.checkState() == Qt.Unchecked:
            newTable = self.makeTable(self.data, self.attributes)
            self.updateTable(newTable)
        else:
            dataWithoutFirstRow = self.data[1:]
            newTable = self.makeTable(dataWithoutFirstRow, self.attributes)
            self.updateTable(newTable)
    
        dataWithoutFirstRow = self.data[1:]
        self.makeTable(dataWithoutFirstRow, self.attributes)


    """
        makes the openfiledialog: when the file is committed, the table is shown.
        the method prepares also the table to show
    """
    def showOpenFileDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(None, 'Open file', '/')
        #make label
        self.label.clear()
        self.label = QtGui.QLabel(filename, self.qPage)
        self.qPage.initializePath(filename)
        self.grid.addWidget(self.label, 2, 0)

        #open file
        file=open(filename)
        csvreader = csv.reader(file)
        array = list(csvreader)
        self.data = array
        #checkbox
        self.makeCheckBoxForFirstRow()
        #tableview
        self.tableView = self.makeTable(array, self.attributes, False)
        self.setTableViewLayout()

    """ layout of the page with the table 
        above a checkbox, below the table
    """    
    def setTableViewLayout(self):
        self.vLayout = QVBoxLayout()
        self.vLayout.addWidget(self.checkBox)
        self.vLayout.addWidget(self.tableView)
        self.qTablePage.setLayout(self.vLayout)
    
    """
        if the checkbox is checked the first row isn't drawn anymore but used for the delegate
    """
    def updateTable(self, newTable):
        self.vLayout.removeWidget(self.tableView)
        self.vLayout.addWidget(newTable)
        self.tableView = newTable
        self.vLayout.update()
    
    """ the layout for the wizard """
    def makeGridLayout(self):
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)
        self.grid.addWidget(self.openToolBar, 1, 0)
        self.label = QtGui.QLabel('select file', self.qPage)
        self.grid.addWidget(self.label, 2, 0)

    """ make the table for the page"""
    def makeTable(self, data, headerData, firstRow=False):
        # create the view
        tv = QTableView()

        # set the table model
        tm = InputTableModel(data, self.attributes, self.qTablePage)

        tv.setModel(tm)
        CHOICES = self.makeChoices(headerData)

        delegate = ComboBoxEditorDelegate(choices=lambda o:CHOICES, parent=tv )
        tv.setItemDelegateForRow(0,delegate)

        # set the minimum size
        self.setMinimumSize(800, 600)

        # hide grid
        tv.setShowGrid(True)

        # set the font
        font = QFont("Courier New", 20)
        tv.setFont(font)

        # hide vertical header
        vh = tv.verticalHeader()
        vh.setVisible(False)

        # hide horizontal header, the first row will be used as header
        hh = tv.horizontalHeader()
        hh.setVisible(False)

        # set column width to fit contents
        # will fale if to much data
        #tv.resizeColumnsToContents()

        # set row height
        nrows = len(list(data))
        for row in xrange(nrows):
            tv.setRowHeight(row, 18)
        return tv

    """" method for initializing the choices of the delegate. a tuple is returned"""
    def makeChoices(self, choices):
        CHOICES = []
        for i in range(len(choices)):
            CHOICES = CHOICES + [(str(i) , choices[i])]
        return tuple(CHOICES)

    def makeHeader(self, model, header):
        for column in range(len(header)):
            index = model.index(0, column, QModelIndex())
            model.setData(index, QVariant(header[column]))
            # can be done with the delegate, change this!!!!
            #model.setData(index, QVariant(QColor(Qt.gray)), Qt.BackgroundColorRole)

    def makeBody(self, model, data):
        for row in range(len(data)):
            for column in range(len(self.attributes)):
                index = model.index((row+1), column, QModelIndex())
                model.setData(index, QVariant(self.data[row][column]))

    """method returning the imported data"""
    def getImportedData(self):
        return list(self.data)
        
#class InputTableModel(QAbstractTableModel): 
class InputTableModel(QStandardItemModel):
    """ class representing the table """
    def __init__(self, datain, headerData, parent=None, *args): 
#        QAbstractTableModel.__init__(self, parent, *args) 
        table = [headerData] + datain
        QStandardItemModel.__init__(self, len(table), len(headerData), parent, *args) 
        self.fill_up_model(table)
 
    def __init__(self, datain, headerData, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        # the headerdata will be the first row in the table
        # it is impossible to add a delegate to a qheaderview (it is possible but ignored)
        # so add the data to the first row and add there the delegate
        # you can add a (different) delegate for each row
        #self.headerRow = headerData
        self.fill_up_table(datain, headerData)


 
    def fill_up_table(self, datain, headerData, hints = None):
        self.arraydata = list(datain)
        self.arraydata.insert(0, headerData)
        self.fill_up_header(hints)

    def fill_up_header(self, hints):
        #first row of data can be a hint
        print "hints" , hints
        if not hints == None :
            self.arraydata.insert(1, hints)
            #for column in range(len(self.arraydata[0])):
            #    self.setData(self.index(0, column), hints[column], Qt.DisplayRole)
        #if no hints are given, fill up the header with first attribute
        #else:
            #for column in range(len(self.arraydata[0])):
            #    self.setData(self.index(0, column), self.arraydata[0][0], Qt.DisplayRole)

        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def rowCount(self, parent):
        #return len(self.arraydata) + len(self.headerRow[0])
        return   len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid(): 
            return QVariant() 
        elif role != Qt.DisplayRole: 
           return QVariant()
        else:
            return QVariant(QStandardItemModel.data(self, index, role))
        #if headerData != None:
        #     makeHeaderData()
        #TODO, now the table is filled from (row = 0, column = 0)
        # first row will have always a comboboxdelegate (index + 1)
        # second row is maybe a "hint" for the choices of the comboboxdelegate (index + 2)
        # so the actual data starts maybe at the index + 1 or index + 2
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.arraydata[index.row()][index.column()])
 
    def fill_up_model(self, table):
        for row in range(len(table)):
            data = table[row]
            for column in range(len(data)):
                index = self.index(row, column, QModelIndex())
                self.setData(index, QVariant(data[column]))

    
    def setData(self, index, value, role=Qt.ItemIsEditable):
        self.arraydata[index.row()][index.column()] = value

    """every item is editable, so no need to keep it for each object """
    def flags(self, index):
        return Qt.ItemIsEditable


class ImportWizardPage(QtGui.QWizardPage):
    """
        class for the page shown in the wizard
    """
    def __init__(self, parent=None, path=None, *args):
        QWizardPage.__init__(self, parent, *args)
        self.path = path

    def initializePath(self, path):
        self.path = path
        self.emit(QtCore.SIGNAL('completeChanged()'))

    def isComplete(self):
        return self.path != None

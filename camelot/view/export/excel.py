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

import logging
logger = logging.getLogger('camelot.view.export.excel')

from pyExcelerator import *
import datetime

titleFont = Font()              # initializing titleFont Object
headerFont = Font()             # initializing headerFont Object
cellFont = Font()               # initializing cellFont Object

titleFont.name = 'Arial'        # Setting Fonts Name
headerFont.name = 'Arial'
cellFont.name = 'Arial'

titleFont.bold = True           # Setting title font to bold
headerFont.bold = True          # Setting column header font to bold
cellFont.bold = False           # Setting cell font to bold

titleFont.height = 240          # 12*20 = 240 Font Size
headerFont.height = 220         # 10*20 = 240 Font Size
cellFont.height = 220           # 10*20 = 240 Font Size

brdLeft = Borders()                # Defining border which is around header
brdLeft.left = 0x01

brdRight = Borders()                # Defining border which is around header
brdRight.right = 0x01

brdTop = Borders()                # Defining border which is around header
brdTop.top = 0x01

brdBottom = Borders()                # Defining border which is around header
brdBottom.bottom = 0x01

brdTopLeft = Borders()
brdTopLeft.top = 0x01
brdTopLeft.left = 0x01

brdBottomLeft = Borders()
brdBottomLeft.bottom = 0x01
brdBottomLeft.left = 0x01

brdBottomRight = Borders()
brdBottomRight.bottom = 0x01
brdBottomRight.right = 0x01

brdTopRight = Borders()
brdTopRight.top = 0x01
brdTopRight.right = 0x01

dateStyle = XFStyle()


titleStyle = XFStyle()
headerStyle = XFStyle()
cellStyle = XFStyle()
dateStyle = XFStyle()

leftCellStyle = XFStyle()
rightCellStyle = XFStyle()
bottomCellStyle = XFStyle()
topleftCellStyle = XFStyle()
bottomleftCellStyle = XFStyle()
bottomrightCellStyle = XFStyle()
toprightCellStyle = XFStyle()

titleStyle.font = titleFont
headerStyle.font = headerFont
headerStyle.borders = brdTop
cellStyle.font = cellFont

topleftCellStyle.font = headerFont
topleftCellStyle.borders = brdTopLeft

bottomleftCellStyle.font = cellFont
bottomleftCellStyle.borders = brdBottomLeft

bottomrightCellStyle.font = cellFont
bottomrightCellStyle.borders = brdBottomRight

toprightCellStyle.font = headerFont
toprightCellStyle.borders = brdTopRight

leftCellStyle.borders = brdLeft
leftCellStyle.font = cellFont

rightCellStyle.borders = brdRight
rightCellStyle.font = cellFont

bottomCellStyle.borders = brdBottom
bottomCellStyle.font = cellFont

pat1 = Pattern()
pat1.pattern = Pattern.SOLID_PATTERN
pat1.pattern_fore_colour = 0x16
headerStyle.pattern = pat1
topleftCellStyle.pattern = pat1
toprightCellStyle.pattern = pat1

def open_data_with_excel(title, headerList, dataList):
    import sys
    import tempfile
    _xls_fd, xls_fn = tempfile.mkstemp(suffix='.xls')
    write_data_to_excel(xls_fn, title, headerList, dataList)
    from PyQt4 import QtGui, QtCore
    if not 'win' in sys.platform:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl('file://%s' % xls_fn))
    else:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        excel_app = win32com.client.Dispatch("Excel.Application")
        excel_app.Visible = True
        excel_app.Workbooks.Open(xls_fn)

def write_data_to_excel(filename, title, headerList, dataList):
    """
    @param filename: the file to which to save the exported excel
    @param title: title to put in the first row of the genarated excel file
    @param headerList: list of header definitions
    @param dataList: list or generator with the row data
    """
    w = Workbook()
    ws = w.add_sheet('Sheet1')
    ## Writing Title
    ws.write(0, 0, title, titleStyle)                   # Writing Title
    ws.col(0).width = len(title) * 400                  # Setting cell width
    ## Writing Header
    myDataTypeDict = {}            # dictionary of datatype, {columnnumber, Datatype}
    myPrecisionDict = {}        # dictionary of precision , {columnnumber, Precision}
    myLengthDict = {}           # dictionary of length , {columnnumber, length}
    myFormatDict = {}           # dictionary of dateformat , {columnnumber, format}
    for n,desc in enumerate(headerList):
        lst =  desc[1]
        if n==0:
            ws.write(2, n, lst['name'], topleftCellStyle)
        elif n==len(headerList)-1:
            ws.write(2, n, lst['name'], toprightCellStyle)
        else:
            ws.write(2, n, lst['name'], headerStyle)
        if len(lst['name']) < 8:
            ws.col(n).width = 8 *  375
        else:
            ws.col(n).width = len(lst['name']) *  375
        myDataTypeDict[ n ] = lst["python_type"]
        if lst["python_type"] == float:
            myPrecisionDict [ n ] = lst["precision"]    #Populating precision dictionary
        elif lst["python_type"] == datetime.date:
            myFormatDict [ n ] = lst["format"]          #Populating date Format dictionary
        elif lst["python_type"] == str:
            if 'length' in lst:
                myLengthDict [ n ] = lst["length"]          #Populating Column Length dictionary
    ## Writing Data
    row = 3
    column = 0
    valueAddedInSize = 0
    formatStr = '0'
    for dictCounter in dataList:                       # iterating the dataList, having dictionary
        column = 0
        cellStyle.num_format_str = '0'
        for i in range( 0 , len(dictCounter)): #for i in dictCounter:
            valueAddedInSize = 0
            val = dictCounter[i]
            if val != None:
                if not isinstance(val,(str,unicode,int,float,datetime.datetime,datetime.time,datetime.date,
                                       ExcelFormula.Formula) ):
                    val = unicode(val)
                if myDataTypeDict.has_key(column) == True:
                    if myLengthDict.get(column) != None:
                        if len(val) > myLengthDict[ column ]:
                            val = val[0:myLengthDict[ column ]]
                    elif myDataTypeDict[ column ] == str:
                        formatStr = '0'
                    elif myDataTypeDict[ column ] == int:
                        formatStr = '0'
                    elif myDataTypeDict[ column ] == float:
                        formatStr = '0.'
                        for _j in range( 0 , myPrecisionDict[ column ]):
                            formatStr += '0'
                        valueAddedInSize = len(formatStr) # To fit the cell width + 1 (of dot(.))
                    elif myDataTypeDict[ column ] == datetime.date:
                        formatStr = myFormatDict[column]
                        val = datetime.datetime( day = val.day, year = val.year, month = val.month)
                    elif myDataTypeDict[ column ] == bool:
                        formatStr = '0'
                    else:
                        formatStr = '0'
                cellStyle.num_format_str = formatStr
                bottomCellStyle.num_format_str = formatStr
                rightCellStyle.num_format_str = formatStr
                bottomrightCellStyle.num_format_str = formatStr
                leftCellStyle.num_format_str = formatStr
                bottomleftCellStyle.num_format_str = formatStr
            elif val == None:
                val = ' '
            if row - 2  == len(dataList):
                #we re at the bottom row
                if i==0:
                    ws.write(row , column, val , bottomleftCellStyle)
                elif i  == len(dictCounter)-1:
                    ws.write(row , column, val , bottomrightCellStyle)
                else:
                    ws.write(row , column, val , bottomCellStyle)
            else:
                if i==0:
                    ws.write(row , column, val , leftCellStyle)
                elif  i == len(dictCounter)-1:
                    ws.write(row , column, val , rightCellStyle)
                else:
                    ws.write(row , column, val , cellStyle)
            if ws.col(column).width < (len(unicode( val )) )* 300:
                ws.col(column).width = (len(unicode( val )) + valueAddedInSize )* 300
            column = column + 1
        row = row + 1
    w.save(filename)

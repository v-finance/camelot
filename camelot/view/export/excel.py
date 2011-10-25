#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

import logging
import datetime
from decimal import Decimal

LOGGER = logging.getLogger('camelot.view.export.excel')

from camelot.core.utils import ugettext
from camelot.core.conf import settings
from camelot.view.controls import delegates
from camelot.view.utils import local_date_format

# previously used pyExcelerator, but this gave errors opening the generated documents in Excel 2010
from xlwt import Font, Borders, XFStyle, Pattern, Workbook, ExcelFormula

titleFont = Font()              # initializing titleFont Object
headerFont = Font()             # initializing headerFont Object
cellFont = Font()               # initializing cellFont Object

# when you need a specific font or size, declare this in your settings file
fontname = 'Arial'
if hasattr(settings, 'EXPORT_EXCEL_FONT'):
    fontname = settings.EXPORT_EXCEL_FONT
titleFont.name = fontname        # Setting Fonts Name
headerFont.name = fontname
cellFont.name = fontname

title_bold = True
header_bold = True
cell_bold = False
if hasattr(settings, 'EXPORT_EXCEL_TITLE_BOLD'):
    title_bold = settings.EXPORT_EXCEL_TITLE_BOLD
if hasattr(settings, 'EXPORT_EXCEL_HEADER_BOLD'):
    header_bold = settings.EXPORT_EXCEL_HEADER_BOLD
if hasattr(settings, 'EXPORT_EXCEL_CELL_BOLD'):
    cell_bold = settings.EXPORT_EXCEL_CELL_BOLD
titleFont.bold = title_bold           # Setting title font to bold
headerFont.bold = header_bold          # Setting column header font to bold
cellFont.bold = cell_bold           # Setting cell font to bold

titlesize = 240 # 12*20 = 240 Font Size
fontsize = 200# 10*20 = 200 Font Size
if hasattr(settings, 'EXPORT_EXCEL_TITLE_SIZE'):
    titlesize = settings.EXPORT_EXCEL_TITLE_SIZE
if hasattr(settings, 'EXPORT_EXCEL_FONT_SIZE'):
    fontsize = settings.EXPORT_EXCEL_FONT_SIZE
titleFont.height = titlesize          
headerFont.height = fontsize         
cellFont.height = fontsize

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
    import tempfile
    _xls_fd, xls_fn = tempfile.mkstemp(suffix='.xls')
    write_data_to_excel(xls_fn, title, headerList, dataList)
    from PyQt4 import QtGui, QtCore
    QtGui.QDesktopServices.openUrl( QtCore.QUrl.fromLocalFile( xls_fn ) )

def write_data_to_excel(filename, title, headerList, data_list):
    """
    @param filename: the file to which to save the exported excel
    @param title: title to put in the first row of the genarated excel file
    @param headerList: list of header definitions
    @param data_list: list or generator with the row data
    """
    LOGGER.debug(u'write data to excel : %s'%title)
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
    header_delegates = {}
    number_of_columns = len(headerList)
    for n,desc in enumerate(headerList):
        lst =  desc[1]
        header_delegates[n] = lst['delegate']
        if n==0:
            ws.write(2, n, unicode(lst['name']), topleftCellStyle)
        elif n==len(headerList)-1:
            ws.write(2, n, unicode(lst['name']), toprightCellStyle)
        else:
            ws.write(2, n, unicode(lst['name']), headerStyle)
        if len(unicode(lst['name'])) < 8:
            ws.col(n).width = 8 *  375
        else:
            ws.col(n).width = len(unicode(lst['name'])) *  375
        myDataTypeDict[ n ] = lst["python_type"]
        if lst["python_type"] == float:
            myPrecisionDict [ n ] = lst["precision"]    #Populating precision dictionary
        elif issubclass(lst['delegate'], delegates.FloatDelegate):
            myPrecisionDict [ n ] = lst.get("precision", 2)
            myDataTypeDict[ n ] = float
        elif lst["python_type"] == datetime.date or issubclass(lst['delegate'], delegates.DateDelegate):
            myFormatDict [ n ] = lst.get('format', local_date_format())         #Populating date Format dictionary
            myDataTypeDict[ n ] = datetime.date
        elif lst["python_type"] == datetime.datetime or issubclass(lst['delegate'], delegates.DateTimeDelegate):
            myDataTypeDict[ n ] = datetime.datetime
            myFormatDict [ n ] = lst["format"]          #Populating date Format dictionary
        elif lst["python_type"] == str:
            if 'length' in lst:
                myLengthDict [ n ] = lst["length"]          #Populating Column Length dictionary
    ## Writing Data
    row = 3
    valueAddedInSize = 0
    formatStr = '0'
    for data in data_list:                       # iterating the data_list, having dictionary
        cellStyle.num_format_str = '0'
        for column, val in enumerate( data ): #for i in dictCounter:
            valueAddedInSize = 0
            if val != None:
                # make sure translations are tried on types that might have one
                if isinstance(val, (unicode, str)):
                    newval = ugettext(val.capitalize())
                    if newval == val.capitalize():
                        newval = ugettext(val)
                    val = newval
                # this is to handle fields of type code
                if isinstance(val, list):
                    val = '.'.join(val)
                if not isinstance(val,(str,unicode,int,float,
                                       datetime.datetime,datetime.time,datetime.date,
                                       ExcelFormula.Formula, Decimal) ):
                    val = unicode(val)
                if isinstance(val, Decimal):
                    val = float(str(val))
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
                        precision = myPrecisionDict[ column ]
                        if not isinstance( precision, int ):
                            # this might happen when precision is a callable
                            precision = 2
                        for _j in range( 0 , precision ):
                            formatStr += '0'
                        valueAddedInSize = len(formatStr) # To fit the cell width + 1 (of dot(.))
                    elif myDataTypeDict[ column ] == datetime.date or isinstance(header_delegates[column], delegates.DateDelegate):
                        formatStr = myFormatDict[column]
                        val = datetime.datetime( day = val.day, year = val.year, month = val.month)
                    elif myDataTypeDict[ column ] == datetime.datetime:
                        formatStr = myFormatDict[column]
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
            if row - 2  == len(data_list):
                #we re at the bottom row
                if column == 0:
                    ws.write(row , column, val , bottomleftCellStyle)
                elif column  == number_of_columns - 1:
                    ws.write(row , column, val , bottomrightCellStyle)
                else:
                    ws.write(row , column, val , bottomCellStyle)
            else:
                if column == 0:
                    ws.write(row , column, val , leftCellStyle)
                elif column == number_of_columns - 1:
                    ws.write(row , column, val , rightCellStyle)
                else:
                    ws.write(row , column, val , cellStyle)
            if ws.col(column).width < (len(unicode( val )) )* 300:
                ws.col(column).width = (len(unicode( val )) + valueAddedInSize )* 300
            column = column + 1
        row = row + 1
    w.save(filename)



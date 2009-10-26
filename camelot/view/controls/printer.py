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

"""
class to handle printing
"""

import logging
logger = logging.getLogger( 'printer' )

from PyQt4 import QtGui
from camelot.view.model_thread import post

icon = '../art/tango/32x32/apps/system-users.png'

class Printer:
    def __init__( self ):
        self.printer = QtGui.QPrinter()
        self.printer.setPageSize( QtGui.QPrinter.Letter )

    def printView( self, view, parent ):
        import settings
        logger.debug( 'printing table view' )
        dialog = QtGui.QPrintDialog( self.printer, parent )
        if not dialog.exec_():
            return

        client_address = '<br/>'.join( ['2 Azalea St.',
                                       'Fredericksburg',
                                       '22406 VA'] )

        import datetime
        ts = datetime.datetime.today()
        datestring = 'Date: %s/%s/%s' % ( ts.month, ts.day, ts.year )

        view_content = view.toHtml()
        context = {
          'logo' : icon,
          'company_name' : 'Conceptive Engineering',
          'company_address_1' : 'L. Van Bauwelstraat 16',
          'company_address_2' : '2220 Heist-op-den-Berg',
          'city' : 'Belgium',
          'date' : datestring,
          'client_address' : client_address,
          'client_name' : 'Client',
          'content' : view_content,
          'signature' : 'M. Anager'
        }

        from jinja import Environment, FileSystemLoader
        fileloader = FileSystemLoader( settings.CANTATE_TEMPLATES_DIRECTORY )
        e = Environment( loader = fileloader )
        t = e.get_template( 'base.html' )
        html = t.render( context )

        doc = QtGui.QTextDocument()
        doc.setHtml( html )
        doc.print_( self.printer )

    def preview( self, view, parent ):
        logger.debug( 'print preview dialog' )

        def generate_html():
            client_address = '<br/>'.join( ['2 Azalea St.',
                                           'Fredericksburg',
                                           '22406 VA'] )

            import datetime
            ts = datetime.datetime.today()
            datestring = 'Date: %s/%s/%s' % ( ts.month, ts.day, ts.year )

            view_content = view.toHtml()
            context = {
              'logo' : icon,
              'company_name' : 'Conceptive Engineering',
              'company_address_1' : 'L. Van Bauwelstraat 16',
              'company_address_2' : '2220 Heist-op-den-Berg',
              'city' : 'Belgium',
              'date' : datestring,
              'client_address' : client_address,
              'client_name' : 'Client',
              'content' : view_content,
              'signature' : 'M. Anager'
            }

            from jinja import Environment
            from camelot.view.templates import loader
            e = Environment( loader = loader )
            t = e.get_template( 'base.html' )
            html = t.render( context )
            return html

        from camelot.view.export.printer import open_html_in_print_preview_from_gui_thread
        post( generate_html, open_html_in_print_preview_from_gui_thread )

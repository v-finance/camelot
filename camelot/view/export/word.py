import logging
from camelot.view import art

logger = logging.getLogger('camelot.view.export.word')

def open_html_in_word(html, template=art.file_('empty_document.doc'),
                      pre_processor=lambda doc:None,
                      post_processor=lambda doc:None):
    """Open MS Word through COM objects and import the specified html
    into a new document.
    @param html: the html to import
    @param template: the empty word document in which to import the html
    @param post_processor: a function that will be called before importing the
    html, with as its argument the COM Document.     
    @param post_processor: a function that will be called after importing the
    html, with as its argument the COM Document.   
    """
    import tempfile
    import os, sys
    
    html_fd, html_fn = tempfile.mkstemp(suffix='.html')
    html_file = os.fdopen(html_fd, 'wb')
    html_file.write(html.encode('utf-8'))
    html_file.close()
  
    if 'win' in sys.platform:
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            word_app = win32com.client.Dispatch("Word.Application")
            doc_fd, doc_fn = tempfile.mkstemp(suffix='.doc')
            os.close(doc_fd)
            word_app.Visible = True
            doc = word_app.Documents.Open(template)
            word_app.ActiveDocument.SaveAs(doc_fn)
            section = doc.Sections(1)
            pre_processor(doc)
            section.Range.InsertFile(FileName=html_fn)
            post_processor(doc)
            doc.Activate()
            word_app.Activate()
        except Exception, e:
            logger.warn('unable to launch word', exc_info=e)
    else:
        """We're probably not running windows, so let OS handle it (used to be abiword)"""
        from PyQt4 import QtGui, QtCore
        QtGui.QDesktopServices.openUrl(QtCore.QUrl('file://%s' % html_fn)) 
        return
    

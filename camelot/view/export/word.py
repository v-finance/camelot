import logging
logger = logging.getLogger('camelot.view.export.word')

def open_html_in_word(html):
  import tempfile
  import os
  from camelot.view import art
  html_fd, html_fn = tempfile.mkstemp(suffix='.html')
  html_file = os.fdopen(html_fd, 'wb')
  html_file.write(html.encode('utf-8'))
  html_file.close()

  try:
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    word_app = win32com.client.Dispatch("Word.Application")
  except Exception, e:
    """We're probably not running windows, so try abiword"""
    logger.warn('unable to launch word', exc_info=e)
    os.system('abiword "%s"'%html_fn)
    return

  doc_fd, doc_fn = tempfile.mkstemp(suffix='.doc')
  os.close(doc_fd)
  word_app.Visible = True
  doc = word_app.Documents.Open(art.file_('empty_document.doc'))
  word_app.ActiveDocument.SaveAs(doc_fn)
  section = doc.Sections(1)
  section.Range.InsertFile(FileName=html_fn)
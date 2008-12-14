import logging
logger = logging.getLogger('camelot.view.export.outlook')

"""
Functions to send files by email using outlook

After http://win32com.goermezer.de/content/view/227/192/
"""
def open_html_in_outlook(html):
  from camelot.view import art
  
  try:
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    outlook_app = win32com.client.Dispatch("Outlook.Application")
  except Exception, e:
    """We're probably not running windows"""
    logger.warn('unable to launch Outlook', exc_info=e)
    return
  
  
  msg = outlook_app.CreateItem(0)
  msg.Body = html

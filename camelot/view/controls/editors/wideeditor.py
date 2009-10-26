class WideEditor(object):
    """Class signaling that an editor, is a wide editor, so it's label should be displayed
  on top of the editor and the editor itself should take two columns::

    class WideTextLineEditor(TextLineEditor, WideEditor):
      pass

  will generate a test line editor where the text line takes the whole with of the
  form"""

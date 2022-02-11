#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
import typing

from camelot.admin.action import ActionStep
from camelot.view.action_runner import hide_progress_dialog
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _
from camelot.view.qml_view import qml_action_step

from dataclasses import dataclass, field

from ...core.serializable import DataclassSerializable
from ...core.qt import QtWidgets

@dataclass
class SelectFile( ActionStep, DataclassSerializable ):
    """Select one or more files to open
    
    :param file_name_filter: Filter on the names of the files that can
        be selected, such as 'All files (*)'.  
        See :class:`QtWidgets.QFileDialog` for more documentation.
    
    .. attribute:: single
    
        defaults to :const:`True`, set to :const:`False` if selection
        of multiple files is allowed
         
    .. attribute:: caption

        The text to display to the user
        
    The :keyword:`yield` statement of :class:`SelectFile` returns a list
    of selected file names.  This list has only one element when single is
    set to :const:`True`.  Raises a 
    :class:`camelot.core.exception.CancelRequest` when no file was selected.
    
    This action step stores its last location into the :class:`QtCore.QSettings` 
    and uses it as the initial location the next time it is invoked.
    """

    file_name_filter: str = ''
    single: bool = True

    caption = _('Open')

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        with hide_progress_dialog(gui_context):
            response = qml_action_step(gui_context, 'SelectFile', serialized_step)
            selected = response['selected']
            if selected:
                return selected
            else:
                raise CancelRequest()

@dataclass
class SaveFile( ActionStep, DataclassSerializable ):
    """Select a file for saving
    
    :param file_name_filter: Filter on the names of the files that can
        be selected, such as 'All files (*)'.  
        See :class:`QtWidgets.QFileDialog` for more documentation.

    :param file_name: `None` or the default filename to use

    .. attribute:: caption

        The text to display to the user

    The :keyword:`yield` statement of :class:`SaveFile` returns a file name.
    Raises a :class:`camelot.core.exception.CancelRequest` when no file was
    selected.
    
    This action step stores its last location into the :class:`QtCore.QSettings` 
    and uses it as the initial location the next time it is invoked.
    """

    file_name_filter: str = ''
    file_name: typing.Optional[str] = None

    caption = _('Save')

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        with hide_progress_dialog(gui_context):
            response = qml_action_step(gui_context, 'SaveFile', serialized_step)
            selected = response['selected']
            if selected:
                return selected
            else:
                raise CancelRequest()

@dataclass
class SelectDirectory(ActionStep, DataclassSerializable):
    """Select a single directory

    .. attribute:: caption

        The text to display to the user

    .. attribute:: options

        options to pass to :meth:`QtWidgets.QFileDialog.getExistingDirectory`,
        defaults to :const:`QtWidgets.QFileDialog.Options.ShowDirsOnly`

    """

    directory: typing.Optional[str] = None
    options: list = field(default_factory=lambda: [QtWidgets.QFileDialog.Option.ShowDirsOnly])

    caption = _('Select directory')

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        with hide_progress_dialog(gui_context):
            response = qml_action_step(gui_context, 'SelectDirectory', serialized_step)
            selected = response['selected']
            if selected:
                return selected
            else:
                raise CancelRequest()

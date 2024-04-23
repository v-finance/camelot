from dataclasses import dataclass
import logging
import typing

from . import gui_naming_context
from ..core.exception import CancelRequest
from ..core.naming import CompositeName, NameNotFoundException
from ..core.serializable import NamedDataclassSerializable

LOGGER = logging.getLogger('camelot.view.responses')


@dataclass
class AbstractResponse(NamedDataclassSerializable):
    """
    Serialiazable Responses the model can send to the UI
    """

    @classmethod
    def _was_canceled(cls, gui_context_name):
        """raise a :class:`camelot.core.exception.CancelRequest` if the
        user pressed the cancel button of the progress dialog in the
        gui_context.
        """
        from ..core.backend import is_cpp_gui_context_name
        if is_cpp_gui_context_name(gui_context_name):
            # @TODO : check was canceled for cpp
            return
        try:
            gui_context = gui_naming_context.resolve(gui_context_name)
        except NameNotFoundException:
            return
        if gui_context is None:
            return
        progress_dialog = gui_context.get_progress_dialog()
        if (progress_dialog is not None) and (progress_dialog.wasCanceled()):
            LOGGER.debug( 'progress dialog was canceled, raise request' )
            # @todo : to avoid a second raise of a cancelrequest, reset
            #         the dialog, this might hide the dialog, even if the
            #         cancel request is not accepted.
            progress_dialog.reset()
            raise CancelRequest()


@dataclass
class Busy(AbstractResponse):
    busy: bool


@dataclass
class ActionStepped(AbstractResponse):
    run_name: CompositeName
    gui_run_name: CompositeName
    # @todo : blocking should be a correlation id instead of a bool, so
    # the server can validate if the response is for the correct step
    blocking: bool
    step: NamedDataclassSerializable


@dataclass
class ActionStopped(AbstractResponse):
    run_name: CompositeName
    gui_run_name: CompositeName
    exception: typing.Any

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
"""
Camelot unittest helpers.  This module contains helper classes and functions
to write unittests for Camelot applications.  These are not the unittests for
Camelot itself. 
"""

import collections
import logging
import unittest
import sys
import os
import json


from ..admin.action.base import Action, MetaActionStep
from ..core.naming import initial_naming_context
from ..core.qt import Qt, QtCore, QtGui, QtWidgets
from ..core.backend import get_root_backend
from ..view.model_process import ModelProcess
from ..view import action_steps

has_programming_error = False

LOGGER = logging.getLogger('camelot.test')

test_context = initial_naming_context.bind_new_context('test', immutable=True)

class GrabMixinCase(object):
    """
    Methods to grab views to pixmaps during unittests
    """

    images_path = ''

    def grab_widget(self, widget, suffix=None, subdir=None):
        """Save a widget as a png file :
    :param widget: the widget to take a screenshot of
    :param suffix: string to add to the default filename of the image
    :param subdir: subdirectory of images_path in which to put the image file, defaults to
        the name of the test class
    - the name of the png file is the name of the test case, without 'test_'
    - it is stored in the directory with the same name as the class, without 'test'
        """
        if not subdir:
            images_path = os.path.join(self.images_path, self.__class__.__name__.lower()[:-len('Test')])
        else:
            images_path = os.path.join(self.images_path, subdir)
        if not os.path.exists(images_path):
            os.makedirs(images_path)
        
        # try to move up in the stack until we find a test method
        for i in range(1, 10):
            if sys._getframe(i).f_code.co_name.startswith('test'):
                break
            
        test_case_name = sys._getframe(i).f_code.co_name[5:]
        image_name = '%s.png'%test_case_name
        if suffix:
            image_name = '%s_%s.png'%(test_case_name, suffix)
        widget.adjustSize()
        widget.repaint()
        QtWidgets.QApplication.sendPostedEvents()
        widget.repaint()
        inner_pixmap = QtWidgets.QWidget.grab(widget)
        # add a border to the image
        border = 4
        outer_image = QtGui.QImage(inner_pixmap.width()+2*border, inner_pixmap.height()+2*border, QtGui.QImage.Format.Format_RGB888)
        outer_image.fill(Qt.GlobalColor.gray)
        painter = QtGui.QPainter()
        painter.begin(outer_image)
        painter.drawPixmap(QtCore.QRectF(border, border, inner_pixmap.width(), inner_pixmap.height()), 
                          inner_pixmap,
                          QtCore.QRectF(0, 0, inner_pixmap.width(), inner_pixmap.height()))
        painter.end()
        outer_image.save(os.path.join(images_path, image_name), 'PNG')

# make sure the name is reserved, so we can unbind it without exception
test_action_name = test_context.bind(('test_action',), object())

class GetActionState(Action):

    def model_run(self, model_context, mode):
        action = initial_naming_context.resolve(tuple(mode))
        yield action_steps.UpdateProgress(
            'Got state', detail=action.get_state(model_context),
        )

get_action_state_name = test_context.bind(('get_action_state',), GetActionState())

class ActionMixinCase(object):
    """
    Helper methods to simulate running actions in a different thread
    """

    def get_state(self, action_name, gui_context):
        """
        Get the state of an action in the model thread and return
        the result.
        """
        recorded_steps = self.gui_run(
            get_action_state_name, mode=action_name,
            model_context_name=self.model_context_name
        )
        assert len(recorded_steps)
        for step_type, step_data in recorded_steps:
            if step_type == action_steps.UpdateProgress.__name__:
                return step_data['detail']
        assert False

    @classmethod
    def gui_run(cls,
                action_name,
                gui_context_name=('constant', 'null'),
                mode=None,
                replies={},
                model_context_name=('constant', 'null')):
        """
        Runs an action and simulates replies by the user each time
        a blocking action step is presented.
        """
        gui_run_name = get_root_backend().run_action(
            gui_context_name, action_name, model_context_name, mode
        )
        cls._replies[tuple(gui_run_name)] = replies
        get_root_backend().action_runner().waitForCompletion()
        return cls._recorded_steps[tuple(gui_run_name)]


class RunningProcessCase(unittest.TestCase, ActionMixinCase):
    """
    Test case that starts a model thread when setting up the case class.

    Overwrite the process_cls class variable with a ModelProcess subclass
    that initialized the needed resources to run the test case.
    """

    process_cls = None

    @classmethod
    def setUpClass(cls):
        cls.thread = cls.process_cls()
        assert isinstance(cls.thread, ModelProcess)
        cls._recorded_steps = collections.defaultdict(list)
        cls._replies = collections.defaultdict(dict)
        get_root_backend().actionStepped.connect(cls._record_step)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        get_root_backend().actionStepped.disconnect(cls._record_step)
        try:
            cls.process()
        finally:
            cls.thread.stop()

    def tearDown(self):
        self.process()
        

    @classmethod
    def _record_step(cls, gui_run_name, action_step_type, gui_context_name, blocking, action_step):
        step = json.loads(action_step.data())
        cls._recorded_steps[tuple(gui_run_name)].append(
            (action_step_type, step)
        )
        replies = cls._replies[tuple(gui_run_name)]
        step_cls = MetaActionStep.action_steps[action_step_type]
        if blocking:
            result = replies.get(step_cls)
            # the result needs to be convertible to a QJsonValue
            assert isinstance(result, (dict, int, float, str, list, type(None)))
            get_root_backend().action_step_result_valid(gui_run_name, result, False, "")

    @classmethod
    def process(cls):
        """Wait until all events are processed and the queues of the model thread are empty"""
        completed = get_root_backend().action_runner().waitForCompletion()
        assert completed

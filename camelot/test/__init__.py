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

import logging
import unittest
import sys
import os

from ..admin.action.base import ActionStep
from ..core.qt import Qt, QtCore, QtGui, QtWidgets
from ..view.action_steps.orm import AbstractCrudSignal
from ..view.action_runner import ActionRunner
from ..view.model_process import ModelProcess
from ..view import model_thread
from ..view.model_thread.signal_slot_model_thread import SignalSlotModelThread

has_programming_error = False

LOGGER = logging.getLogger('camelot.test')

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
        QtWidgets.QApplication.flush()
        widget.repaint()
        inner_pixmap = QtWidgets.QWidget.grab(widget)
        # add a border to the image
        border = 4
        outer_image = QtGui.QImage(inner_pixmap.width()+2*border, inner_pixmap.height()+2*border, QtGui.QImage.Format_RGB888)
        outer_image.fill(Qt.gray)
        painter = QtGui.QPainter()
        painter.begin(outer_image)
        painter.drawPixmap(QtCore.QRectF(border, border, inner_pixmap.width(), inner_pixmap.height()), 
                          inner_pixmap,
                          QtCore.QRectF(0, 0, inner_pixmap.width(), inner_pixmap.height()))
        painter.end()
        outer_image.save(os.path.join(images_path, image_name), 'PNG')

class ActionMixinCase(object):
    """
    Helper methods to simulate running actions in a different thread
    """

    @classmethod
    def get_state(cls, action, gui_context):
        """
        Get the state of an action in the model thread and return
        the result.
        """
        model_context = gui_context.create_model_context()

        class StateRegister(QtCore.QObject):

            def __init__(self):
                super(StateRegister, self).__init__()
                self.state = None

            @QtCore.qt_slot(object)
            def set_state(self, state):
                self.state = state

        state_register = StateRegister()
        cls.thread.post(
            action.get_state, state_register.set_state, args=(model_context,)
        )
        cls.process()
        return state_register.state

    @classmethod
    def gui_run(cls, action, gui_context):
        """
        Simulates the gui_run of an action, but instead of blocking,
        yields progress each time a message is received from the model.
        """

        class IteratingActionRunner(ActionRunner):

            def __init__(self, generator_function, gui_context):
                super(IteratingActionRunner, self).__init__(
                    generator_function, gui_context
                )
                self.return_queue = []
                self.exception_queue = []
                cls.process()

            @QtCore.qt_slot( object )
            def generator(self, generator):
                LOGGER.debug('got generator')
                self._generator = generator

            @QtCore.qt_slot( object )
            def exception(self, exception_info):
                LOGGER.debug('got exception {}'.format(exception_info))
                self.exception_queue.append(exception_info)

            @QtCore.qt_slot( object )
            def __next__(self, yielded):
                LOGGER.debug('got step {}'.format(yielded))
                self.return_queue.append(yielded)

            def run(self):
                super(IteratingActionRunner, self).generator(self._generator)
                cls.process()
                step = self.return_queue.pop()
                while isinstance(step, ActionStep):
                    if isinstance(step, AbstractCrudSignal):
                        LOGGER.debug('crud step, update view')
                        step.gui_run(gui_context)
                    LOGGER.debug('yield step {}'.format(step))
                    gui_result = yield step
                    LOGGER.debug('post result {}'.format(gui_result))
                    cls.thread.post(
                        self._iterate_until_blocking,
                        self.__next__,
                        self.exception,
                        args = (self._generator.send, gui_result,)
                    )
                    cls.process()
                    if len(self.exception_queue):
                        raise Exception(self.exception_queue.pop().text)
                    step = self.return_queue.pop()
                LOGGER.debug("iteration finished")
                yield None

        runner = IteratingActionRunner(action.model_run, gui_context)
        yield from runner.run()


class RunningThreadCase(unittest.TestCase, ActionMixinCase):
    """
    Test case that starts a model thread when setting up the case class
    """

    @classmethod
    def setUpClass(cls):
        cls.thread = SignalSlotModelThread()
        model_thread._model_thread_.insert(0, cls.thread)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        model_thread._model_thread_.remove(cls.thread)
        cls.thread.stop()

    @classmethod
    def process(cls):
        """Wait until all events are processed and the queues of the model thread are empty"""
        cls.thread.wait_on_work()
        QtCore.QCoreApplication.instance().processEvents()

class RunningProcessCase(unittest.TestCase, ActionMixinCase):
    """
    Test case that starts a model thread when setting up the case class
    """

    @classmethod
    def setUpClass(cls):
        cls.thread = ModelProcess()
        model_thread._model_thread_.insert(0, cls.thread)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        model_thread._model_thread_.remove(cls.thread)
        cls.thread.stop()

    @classmethod
    def process(cls):
        """Wait until all events are processed and the queues of the model thread are empty"""
        cls.thread.wait_on_work()
        QtCore.QCoreApplication.instance().processEvents()
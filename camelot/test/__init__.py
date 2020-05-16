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

from ..core.qt import Qt, QtCore, QtGui, QtWidgets
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

class RunningThreadCase(unittest.TestCase):
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

class RunningProcessCase(unittest.TestCase):
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
import unittest

from camelot.view.model_thread import signal_slot_model_thread

class ModelThreadCase( unittest.TestCase ):
    
    def test_task( self ):
        
        def normal_request():
            pass
        
        task = signal_slot_model_thread.Task( normal_request )
        task.execute()
        
        def exception_request():
            raise Exception()
        
        task = signal_slot_model_thread.Task( exception_request )
        task.execute()
        
        def iterator_request():
            raise StopIteration()
        
        task = signal_slot_model_thread.Task( iterator_request )
        task.execute()
        
        def unexpected_request():
            raise SyntaxError()
        
        task = signal_slot_model_thread.Task( unexpected_request )
        task.execute()
        
    def test_task_handler( self ):
        queue = [None, signal_slot_model_thread.Task( lambda:None )]
        task_handler = signal_slot_model_thread.TaskHandler( queue )
        task_handler.handle_task()
        self.assertEqual( len( queue ), 0 )
        
    def test_model_thread( self ):
        mt = signal_slot_model_thread.SignalSlotModelThread( lambda:None )
        mt.post( lambda:None )

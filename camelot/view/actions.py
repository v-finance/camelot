
def model_thread_action(name, model_thread_function):
  """
  Create an action method for a method that needs to be
  executed in the model thread.
  @param model_thread_function: a function taking as a single
  argument the object on which the action takes place
  @return: a function that can run in the gui thread and will
  initiate the model_thread_action function in the model thread.
  this resulting function takes as a single argument a function
  returning the model object 
  
  To be used within the definition of Admin classes.
  
  def launch(shuttle):
    print 'lift off', shuttle.name
    
  class Admin(EntityAdmin):
    actions = [model_thread_action('Launch space shuttle', launch)]
    
  """
  def gui_thread_action(entity_getter):
    
    from PyQt4 import QtGui, QtCore
    
    progress = QtGui.QProgressDialog('Please wait', QtCore.QString(), 0, 0)
    progress.setWindowTitle(name)
    progress.show()
    
    def create_request(entity_getter):
      
      def request():
        o = entity_getter()
        model_thread_function(o)
        
      return request
    
    def exception(exc):
      progress.close()
       
    from camelot.view.model_thread import get_model_thread
    mt = get_model_thread()
    mt.post(create_request(entity_getter), lambda *a:progress.close(), exception=exception)
      
  return (name, gui_thread_action)
# begin camelot imports
from camelot.admin.action import Action
from camelot.view import action_steps
from camelot.view.main import main_action
# end camelot imports

# begin application definition
class HelloWorld(Action):

    def model_run(self, model_context):
        yield action_steps.MessageBox(u'Hello World')
# end application definition

# begin application start magic
if __name__=='__main__':
    hello_world = HelloWorld()
    main_action(hello_world)
# end application start magic


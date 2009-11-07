from camelot.admin.validator.entity_validator import EntityValidator
from camelot.admin.entity_admin import EntityAdmin

class PersonValidator(EntityValidator):

    def objectValidity(self, entity_instance):
        messages = super(PersonValidator,self).objectValidity(entity_instance)
        if (not entity_instance.first_name) or (len(entity_instance.first_name) < 3):
            messages.append("A person's first name should be at least 2 characters long")
        return messages
    
class Admin(EntityAdmin):
    verbose_name = 'Person'
    list_display = ['first_name', 'last_name']
    validator = PersonValidator    

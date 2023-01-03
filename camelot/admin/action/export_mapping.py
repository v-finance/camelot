import dataclasses

from .base import Action
from ..icon import CompletionValue
from camelot.core.utils import ugettext_lazy as _
from camelot.view import action_steps
from camelot.admin.dataclass_admin import DataclassAdmin
from camelot.core.dataclasses import dataclass
from camelot.core.naming import initial_naming_context

@dataclass
class ExportMappingOptions(object):
    
    name: str = dataclasses.field(default = None, init = False)

    class Admin(DataclassAdmin):
        list_display = ['name']

class SaveExportMapping( Action ):
    """
    Save the user defined order of columns to export
    """

    verbose_name = _('Save')
    tooltip = _('Save the order of the columns for future use')
    name = 'save_mapping'

    def __init__(self, settings):
        self.settings = settings

    def read_mappings(self):
        self.settings.sync()
        mappings = dict()
        number_of_mappings = self.settings.beginReadArray('mappings')
        for i in range(number_of_mappings):
            self.settings.setArrayIndex(i)
            name = self.settings.value('name', b'')
            number_of_columns = self.settings.beginReadArray('columns')
            columns = list()
            for j in range(number_of_columns):
                self.settings.setArrayIndex(j)
                field = self.settings.value('field', b'')
                columns.append(field)
            self.settings.endArray()
            mappings[name] = columns
        self.settings.endArray()
        return mappings

    def write_mappings(self, mappings):
        self.settings.beginWriteArray('mappings')
        for i, (name, columns) in enumerate(mappings.items()):
            self.settings.setArrayIndex(i)
            self.settings.setValue('name', name)
            self.settings.beginWriteArray('columns')
            for j, column in enumerate(columns):
                self.settings.setArrayIndex(j)
                self.settings.setValue('field', column)
            self.settings.endArray()
        self.settings.endArray()
        self.settings.sync()

    def mapping_items(self, mappings):
        items = [CompletionValue(initial_naming_context._bind_object(None), '')]
        for mapping_name in mappings.keys():
            items.append(CompletionValue(
                value = initial_naming_context._bind_object(mapping_name),
                verbose_name = mapping_name
            ))
        return items

    def model_run(self, model_context, mode):
        if model_context.collection_count:
            mappings = self.read_mappings()
            options = ExportMappingOptions()
            app_admin = model_context.admin.get_application_admin()
            options_admin = app_admin.get_related_admin(ExportMappingOptions)
            yield action_steps.ChangeObject(options, options_admin)
            columns = [column_mapping.field for column_mapping in model_context.get_collection() if column_mapping.field]
            mappings[options.name] = columns
            self.write_mappings(mappings)

class RestoreExportMapping( SaveExportMapping ):
    """
    Restore the user defined order of columns to export
    """

    verbose_name = _('Restore')
    tooltip = _('Restore the previously stored order of the columns')
    name = 'restore_mapping'

    def model_run(self, model_context, mode):
        mappings = self.read_mappings()
        mapping_name_name = yield action_steps.SelectItem(self.mapping_items(mappings))
        mapping_name = initial_naming_context.resolve(mapping_name_name)
        if mapping_name is not None:
            fields = mappings[mapping_name]
            for i, column_mapping in enumerate(model_context.get_collection()):
                if i<len(fields):
                    # the stored field might no longer exist
                    for field, _name in model_context.admin.field_choices:
                        if field==fields[i]:
                            column_mapping.field = fields[i]
                            break
                else:
                    column_mapping.field = None
            yield action_steps.UpdateObjects(model_context.get_collection())

class RemoveExportMapping( SaveExportMapping ):
    """
    Remove a user defined order of columns to export
    """

    verbose_name = _('Remove')
    tooltip = _('Remove the previously stored order of the columns')
    name = 'remove_mapping'

    def model_run(self, model_context, mode):
        mappings = self.read_mappings()
        mapping_name_name = yield action_steps.SelectItem(self.mapping_items(mappings))
        mapping_name = initial_naming_context.resolve(mapping_name_name)
        if mapping_name is not None:
            mappings.pop(mapping_name)
            self.write_mappings(mappings)

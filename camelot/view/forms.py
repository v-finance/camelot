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

"""Classes to layout fields on a form.  These are mostly used for specifying the
form_display attribute in Admin classes, but they can be used on their own as
well.  Form classes can be used recursive.
"""
import dataclasses
import logging
from typing import Any, Literal

from dataclasses import dataclass, InitVar

from ..core.serializable import NamedDataclassSerializable

logger = logging.getLogger('camelot.view.forms')

class AbstractFormElement(NamedDataclassSerializable):
    pass

@dataclass
class AbstractForm(AbstractFormElement):
    """
    Base Form class to put fields on a form.  The base class of a form is
    a list.  So the form itself is nothing more than a list of field names or
    sub-forms.  A form can thus be manipulated using the list's method such as
    append or insert.
    
    Forms are defined using the `form_display` attribute of an `Admin` class::
    
        class Admin( EntityAdmin ):
            form_display = Form( [ 'title', 'short_description', 
                                   'release_date' ] )
                                   
    and takes these parameters :
    
        :param content: an iterable with field names or sub-forms to render
        :param columns: the number of columns in which to order the fields.
    
    .. image:: /_static/form/form.png
    
    """
    title: str = dataclasses.field(init=False)
    content: list = dataclasses.field(init=False)
    scrollbars: bool = dataclasses.field(init=False, default=False)
    columns: int = dataclasses.field(init=False, default=1)

    def get_fields(self):
        """:return: the fields, visible in this form"""
        return [field for field in self._get_fields_from_form()]

    def _get_fields_from_form(self):
        for field in self.content:
            if field is None:
                continue
            elif issubclass(type(field), AbstractForm):
                for nested_field in field._get_fields_from_form():
                    yield nested_field
            elif not isinstance(field, AbstractFormElement):
                assert isinstance(field, str) or (field is None)
                yield field
    
    def __str__(self):
        return 'AbstractForm(%s)' % (u','.join(str(c) for c in self.content))


@dataclass
class Form(AbstractForm):
    title: str = dataclasses.field(init=False, default=None)
    content: list
    scrollbars: bool = False
    columns: int = 1
    rows: int = 1

@dataclass
class Break(AbstractFormElement):
    """End a line in a multi-column form"""
    pass

@dataclass
class Label(AbstractFormElement):
    """Render a label using a :class:`QtWidgets.QLabel`
            :param label : string to be displayed in the label
            :param alignment : alignment of text in the label. values that make
                sense 'left', 'right' or 'center'
            :param style : string of cascading stylesheet instructions
    """
    label: str
    alignment: str = 'left'
    style: str = None


@dataclass
class TabForm(AbstractForm):
    """
    Render forms within a :class:`QtWidgets.QTabWidget`::
    
        from = TabForm([('First tab', ['title', 'short_description']),
                        ('Second tab', ['director', 'release_date'])])
    
    .. image:: /_static/form/tab_form.png
    
    :param tabs: a list of tuples of (tab_label, tab_form)
    :param position: the position of the tabs with respect to the pages
    """

    NORTH = 'North'
    SOUTH = 'South'
    WEST = 'West'
    EAST = 'East'

    title: str = dataclasses.field(init=False, default=None)
    tabs: InitVar[list]
    position: Literal[NORTH, SOUTH, WEST, EAST] = NORTH

    def __post_init__(self, tabs):
        assert isinstance(tabs, list)
        assert self.position in [self.NORTH, self.SOUTH, self.WEST, self.EAST]
        for tab in tabs:
            assert isinstance(tab, tuple)
        self.content = [(tab_label, structure_to_form(tab_form)) for tab_label, tab_form in tabs]
    
    @property
    def tabs(self):
        return self.content
    
    def __str__(self):
        return 'TabForm { %s\n        }' % (u'\n  '.join('%s : %s' % (label, str(form)) for label, form in self.tabs))

    def add_tab(self, tab_label, tab_form):
        """Add a tab to the form

        :param tab_label: the name of the tab
        :param tab_form: the form to display in the tab or a list of field names.
        """
        tab_form = structure_to_form(tab_form)
        self.tabs.append((tab_label, tab_form))

    def get_tab(self, tab_label):
        """Get the tab form of associated with a tab_label, use this function to
        modify the underlying tab_form in case of inheritance

        :param tab_label : a label of a tab as passed in the construction method
        :return: the tab_form corresponding to tab_label
        """
        for label, form in self.tabs:
            if label == tab_label:
                return form

    def _get_fields_from_form(self):
        for _label, form in self.tabs:
            for field in form._get_fields_from_form():
                yield field


@dataclass
class HBoxForm(AbstractForm):
    """
  Render different forms in a horizontal box::

    form = forms.HBoxForm([['title', 'short_description'], ['director', 'release_date']])

  .. image:: /_static/form/hbox_form.png

  :param columns: a list of forms to display in the different columns of the horizontal box
  """

    title: str = dataclasses.field(init=False, default=None)
    content: list
    scrollbars: bool = False

    def __post_init__(self):
        assert isinstance(self.content, list)
        self.content = [structure_to_form(col) for col in self.content]
    
    def __str__(self):
        return 'HBoxForm [ %s\n         ]' % ('         \n'.join([str(form) for form in self.content]))

    def _get_fields_from_form(self):
        for form in self.content:
            for field in form._get_fields_from_form():
                yield field


@dataclass
class VBoxForm(AbstractForm):
    """
  Render different forms or widgets in a vertical box::

    form = forms.VBoxForm([['title', 'short_description'], ['director', 'release_date']])
    
  .. image:: /_static/form/vbox_form.png
  
  :param rows: a list of forms to display in the different rows of the vertical box
  """

    title: str = dataclasses.field(init=False, default=None)
    content: list

    def __post_init__(self):
        assert isinstance(self.content, list)
        self.content = [structure_to_form(row) for row in self.content]

    @property
    def rows(self):
        return self.content

    def _get_fields_from_form(self):
        for form in self.content:
            if isinstance(form, AbstractForm):
                for field in form._get_fields_from_form():
                    yield field
    
    def __str__(self):
        return 'VBoxForm [ %s\n         ]' % ('         \n'.join([str(form) for form in self.content]))


@dataclass
class ColumnSpan(AbstractForm):

    title: str = dataclasses.field(init=False, default=None)
    field: InitVar[str] = None
    num: InitVar[int] = 2

    def __post_init__(self, field, num):
        self.content = [field]
        self.columns = num

@dataclass
class GridForm(AbstractForm):
    """Put different fields into a grid, without a label.  Row or column labels can be added
  using the :class:`Label` form::

    GridForm([['title', 'short_description'], ['director','release_date']])
    :param grid: A list for each row in the grid, containing a list with all fields that should be put in that row
  .. image:: /_static/form/grid_form.png
  """

    title: str = dataclasses.field(init=False, default=None)
    grid: InitVar[list]
    nomargins: bool = False

    def __post_init__(self, grid):
        assert isinstance( grid, list )
        fields = []
        for row in grid:
            assert isinstance( row, list )
            fields.extend(row)
        self.content = grid
    
    @property
    def grid(self):
        return self.content
    
    def _get_fields_from_form(self):
        for row in self.grid:
            for field in row:
                if field is None:
                    continue
                elif issubclass(type(field), AbstractForm):
                    for nested_field in field._get_fields_from_form():
                        yield nested_field
                elif not isinstance(field, AbstractFormElement):
                    assert isinstance(field, str) or (field is None)
                    yield field
    
    def append_row(self, row):
        """:param row: the list of fields that should come in the additional row
        use this method to modify inherited grid forms"""
        assert isinstance(row, list)
        self.grid.append(row)

    def append_column(self, column):
        """:param column: the list of fields that should come in the additional column
        use this method to modify inherited grid forms"""
        assert isinstance(column, list)
        for row, additional_field in zip(self.grid, column):
            row.append(additional_field)


@dataclass
class WidgetOnlyForm(AbstractForm):
    """Renders a single widget without its label, typically a one2many widget"""

    title: str = dataclasses.field(init=False, default=None)
    field: InitVar[str]

    def __post_init__(self, field):
        assert isinstance( field, str )
        self.content = [field]

    @property
    def field(self):
        for field in self.content:
            return field


@dataclass
class Stretch(AbstractFormElement):
    """A stretchable space with zero minimum size, this is able to fill a gap
    in the form if there are no other items to fill this space.
    """
    pass

@dataclass
class GroupBoxForm(AbstractForm):
    """
  Renders a form within a QGroupBox::

    class Admin(EntityAdmin):
      form_display = GroupBoxForm('Movie', ['title', 'short_description'])

  .. image:: /_static/form/group_box_form.png
  """
    
    title: str
    content: Any
    scrollbars: bool = None
    min_width: int = None
    min_height: int = None
    columns: int = 1

    def __post_init__(self):
        if issubclass(type(self.content), AbstractFormElement):
            self.content = [self.content]

def structure_to_form(structure):
    """Convert a python data structure to a form, using the following rules :

   * if structure is an instance of Form, return structure
   * if structure is a list, create a Form from this list

  This function is mainly used in the Admin class to construct forms out of
  the form_display attribute
    """
    if issubclass(type(structure), AbstractFormElement):
        return structure
    return Form(structure)

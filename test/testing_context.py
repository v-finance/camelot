#
# This file contains the context required server side to run the unit tests.
# This whole file should be self contained, as it will be send as a string to
# the server and executed there.
#

import datetime
import logging
import time
from pathlib import PurePosixPath

import sqlalchemy
from sqlalchemy import event, insert, Table, ForeignKey, Column, orm
from sqlalchemy.engine import Engine, create_engine

import camelot
from camelot.admin.action import (
    Action, list_action, form_action, application_action, list_filter, Mode
)
from camelot.admin.action.field_action import ClearObject, SelectObject
from camelot.admin.action.logging import ChangeLogging
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.entity_admin import EntityAdmin
from camelot.admin.icon import CompletionValue
from camelot.admin.model_context import ObjectsModelContext
from camelot.admin.object_admin import ObjectAdmin
from camelot.core.files.storage import Storage
from camelot.core.item_model import QueryModelProxy
from camelot.core.naming import initial_naming_context
from camelot.core.orm import Entity, metadata, Session
from camelot.core.qt import QtCore, QtGui
from camelot.core.utils import ugettext_lazy as _
from camelot.test import test_context
from camelot.view.art import ColorScheme
from camelot.view import action_steps, forms
from camelot.view.controls import delegates

LOGGER = logging.getLogger('testing_context')

#
# This creates an in memory database per thread
#

model_engine = create_engine('sqlite://')

#
# Testing model classes
#

class B(object):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return '{}'.format(self.value)

    class Admin(ObjectAdmin):
        list_display = ['value']


class C(B):
    pass

class A(object):

    def __init__(self, x):
        self.w = B(x)
        self.x = x
        self.y = 0
        self.z = [C(0), C(0)]
        self.created = datetime.datetime.now()

    class Admin(ObjectAdmin):
        list_display = ['x', 'y', 'z', 'created', 'w']
        field_attributes = {
            'w': {'editable': True,
                  'delegate': delegates.Many2OneDelegate,
                  'target': B,
                  'actions':[SelectObject(), ClearObject()],
                  },
            'x': {'editable': True,
                  'static':'static',
                  'prefix':lambda o:'pre',
                  'tooltip': 'Hint',
                  'background_color': 'red',
                  'delegate': delegates.IntegerDelegate,
                  },
            'y': {'editable': lambda o: o.x < 10,
                  'delegate': delegates.IntegerDelegate,
                  'nullable': False,
                  },
            'z': {'editable': True,
                  'delegate': delegates.One2ManyDelegate,
                  'target': C,
                  },
            'created': {
                'delegate': delegates.DateTimeDelegate
            }
        }

        def get_verbose_identifier(self, obj):
            return 'A : {0}'.format(obj.x)

        def get_completions(self, obj, field_name, prefix):
            if field_name == 'w':
                return [
                    B('{0}_{1.x}_1'.format(prefix, obj)),
                    B('{0}_{1.x}_2'.format(prefix, obj)),
                    B('{0}_{1.x}_3'.format(prefix, obj)),
                    ]

class FinancialParty(Entity):

    __tablename__ = 'party'

    row_type = Column(sqlalchemy.types.Unicode(30), nullable=False, index=True)
    id = Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False)

    __mapper_args__ = {
        'polymorphic_on': row_type
    }

class Person(FinancialParty):

    __mapper_args__ = {
        'polymorphic_identity': 'person'
    }

    first_name = Column(sqlalchemy.types.Unicode(30))
    last_name = Column(sqlalchemy.types.Unicode(25))

    @property
    def full_name(self) -> str:
        if (self.first_name is not None) and (self.last_name is not None):
            return self.first_name + ' ' + self.last_name

    class Admin(EntityAdmin):
        list_display = ['first_name', 'last_name', 'full_name']

class Organization(FinancialParty):

    __mapper_args__ = {
        'polymorphic_identity': 'organization'
    }

    name = Column(sqlalchemy.types.Unicode(30))

    class Admin(EntityAdmin):
        list_display = ['name']

class Movie( Entity ):

    __tablename__ = 'movies'

    cover_storage = Storage(upload_to=PurePosixPath('covers'))
    script_storage = Storage(upload_to=PurePosixPath('script'))

    title = Column( sqlalchemy.types.Unicode(60), nullable = False )
    short_description = Column( sqlalchemy.types.Unicode(512) )
    releasedate = Column( sqlalchemy.types.Date )
    genre = Column( sqlalchemy.types.Unicode(15) )
    rating = Column( sqlalchemy.types.Integer() )
    #
    # All relation types are covered with their own editor
    #
    director_party_id = Column(sqlalchemy.types.Integer(), ForeignKey(Person.id))
    director = orm.relationship(Person)

# end short movie definition
    #
    # Camelot includes custom sqlalchemy types, like Image, which stores an
    # image on disk and keeps the reference to it in the database.
    #
# begin image definition
    cover = Column(camelot.types.File(cover_storage))
# end image definition
    #
    # Or File, which stores a file in the upload_to directory and stores a
    # reference to it in the database
    #
    script = Column(camelot.types.File(script_storage))
    description = Column( camelot.types.RichText )

    #
    # Each Entity subclass can have a subclass of EntityAdmin as
    # its inner class.  The EntityAdmin class defines how the Entity
    # class will be displayed in the GUI.  Its behavior can be steered
    # by specifying some class attributes
    #
    # To fully customize the way the entity is visualized, the EntityAdmin
    # subclass should overrule some of the EntityAdmin's methods
    #
    bar = 3
    class Admin(EntityAdmin):
        # the list_display attribute specifies which entity attributes should
        # be visible in the table view
        list_display = ['cover', 'title', 'releasedate', 'rating',]
        lines_per_row = 5
        # if the search function needs to look in related object attributes,
        # those should be specified within list_search
        list_search = ['director.full_name']
        # begin list_actions
        #
        # the action buttons that should be available in the list view
        #
        list_actions = []
        # end list_actions
        drop_action = None
        # the form_display attribute specifies which entity attributes should be
        # visible in the form view
        form_display = forms.TabForm([
          ('Movie', forms.Form([
            forms.HBoxForm([forms.WidgetOnlyForm('cover'), ['title', 'rating', forms.Stretch()]]),
            'short_description',
            'releasedate',
            'director',
            'script',
            'genre',
            'description',], columns = 2)),
          ('Cast', forms.WidgetOnlyForm('cast')),
          ('Tags', forms.WidgetOnlyForm('tags'))
        ])

        # begin form_actions
        #
        # create a list of actions available for the user on the form view
        #
        form_actions = []
        # end form_actions
        #
        # additional attributes for a field can be specified in the
        # field_attributes dictionary
        #
        field_attributes = dict(cast=dict(create_inline=True),
                                genre=dict(editable=lambda o:bool(o.title and len(o.title))),
                                releasedate=dict(background_color=lambda o:ColorScheme.orange_1 if o.releasedate and o.releasedate < datetime.date(1920,1,1) else None),
                                rating=dict(tooltip='''<table>
                                                          <tr><td>1 star</td><td>Not that good</td></tr>
                                                          <tr><td>2 stars</td><td>Almost good</td></tr>
                                                          <tr><td>3 stars</td><td>Good</td></tr>
                                                          <tr><td>4 stars</td><td>Very good</td></tr>
                                                          <tr><td>5 stars</td><td>Awesome !</td></tr>
                                                       </table>'''),
                                script=dict(remove_original=True))

    def __unicode__(self):
        return self.title or ''

# define filters to be available in the table view
Movie.Admin.list_filter = [
    list_filter.GroupBoxFilter(Movie.genre),
    list_filter.GroupBoxFilter(Person.last_name, joins=[Movie.director])
]

class Cast( Entity ):
    
    __tablename__ = 'cast'

    role = Column( sqlalchemy.types.Unicode(60) )
    movie_id = Column(sqlalchemy.types.Integer(), ForeignKey(Movie.id), nullable=False)
    movie = orm.relationship(Movie, backref='cast')
    actor_id = Column(sqlalchemy.types.Integer(), ForeignKey(Person.id), nullable=False)
    actor = orm.relationship(Person)

    class Admin( EntityAdmin ):
        verbose_name = 'Actor'
        list_display = ['actor', 'role']

    def __unicode__(self):
        if self.actor:
            return self.actor.last_name
        return ''

class Tag(Entity):

    __tablename__ = 'tags'

    name = Column( sqlalchemy.types.Unicode(60), nullable = False )

    def __unicode__( self ):
        return self.name

    class Admin( EntityAdmin ):
        form_size = (400,200)
        list_display = ['name']

t = Table('tags_movies__movies_tags', metadata, Column('movies_id', sqlalchemy.types.Integer(), ForeignKey(Movie.id), primary_key=True),
          Column('tags_id', sqlalchemy.types.Integer(), ForeignKey(Tag.id), primary_key=True))
Tag.movies = orm.relationship(Movie, backref='tags', secondary=t, foreign_keys=[t.c.movies_id, t.c.tags_id])

#
# Testing data
#

def load_movie_fixtures(connection):

    connection.execute(insert(Person.__table__),[
        {"id": 1, "row_type": "person", "first_name": "Stanley", "last_name": "Kubrick",},
        {"id": 2, "row_type": "person", "first_name": "Doug", "last_name": "Liman",},
        {"id": 3, "row_type": "person", "first_name": "Martin", "last_name": "Campbell"},
        {"id": 4, "row_type": "person", "first_name": "John", "last_name": "Lasseter"},
        {"id": 5, "row_type": "person", "first_name": "Chris", "last_name": "Columbus"},
        ],)

    connection.execute(insert(Movie.__table__),[
        {
            "title": 'The Shining',
            "short_description": 'The tide of terror that swept America is here.',
            "releasedate": datetime.date(1980, 5, 23),
            "director_id": 1,
            "genre": 'thriller',
            "rating": 4,
            "description": 'A family heads to an isolated hotel for the winter where an evil'
            ' and spiritual presence influences the father into violence,'
            ' while his psychic son sees horrific forebodings from the past'
            ' and of the future.'
        }, {
            "title": 'The Bourne Identity',
            "short_description": 'Matt Damon is Jason Bourne.',
            "releasedate": datetime.date(2002, 6, 14),
            "director_id": 2,
            "genre": 'action',
            "rating": 4,
            "description": 'A man is picked up by a fishing boat, bullet-riddled and without'
            ' memory, then races to elude assassins and recover from amnesia.'
        }, {
            "title": 'Casino Royale',
            "short_description": 'Discover how James became Bond.',
            "releasedate": datetime.date(2006, 11, 17),
            "director_id": 3,
            "genre": 'action',
            "rating": 5,
            "description": "In his first mission, James Bond must stop Le Chiffre, a banker"
            " to the world's terrorist organizations, from winning a"
            " high-stakes poker tournament at Casino Royale in Montenegro."
        }, {
            "title": 'Toy Story',
            "short_description": 'Oooh...3-D.',
            "releasedate": datetime.date(1995, 11, 22),
            "director_id": 4,
            "genre": 'animation',
            "rating": 4,
            "description": "a cowboy toy is profoundly threatened and jealous when a fancy"
            " spaceman toy supplants him as top toy in a boy's room."
        }, {
            "title": "Harry Potter and the Sorcerer's Stone",
            "short_description": 'Let The Magic Begin.',
            "releasedate": datetime.date(2001, 11, 16),
            "director_id": 5,
            "genre": 'family',
            "rating": 3,
            "description": 'Rescued from the outrageous neglect of his aunt and uncle, a'
            ' young boy with a great destiny proves his worth while attending'
            ' Hogwarts School of Witchcraft and Wizardry.'
        },
    ])

    connection.execute(insert(Tag.__table__),[
        {"id": 1, "name": "Drama",},
        ],)

app_admin = ApplicationAdmin()

unit_test_context = initial_naming_context.bind_new_context(
    'unit_test', immutable=True
)

#
# Testing actions
#

class SetupProxy(Action):

    def model_run(self, model_context, mode):
        admin = app_admin.get_related_admin(A)
        proxy = admin.get_proxy([A(0), A(1), A(2)])
        model_context = ObjectsModelContext(admin, proxy, QtCore.QLocale())
        initial_naming_context.rebind(tuple(mode), model_context)
        id_collection = [id(a) for a in proxy.get_model()]
        created_collection = [a.created.second for a in proxy.get_model()]
        yield action_steps.UpdateProgress(
            text='Proxy setup', detail={
                'id_collection': id_collection,
                'created_collection': created_collection,
            }
        )

setup_proxy_name = test_context.bind(('setup_proxy',), SetupProxy())

class GetData(Action):

    def model_run(self, model_context, mode):
        index_in_collection, attribute, data_is_collection = mode
        collection = model_context.proxy.get_model()
        data = getattr(collection[index_in_collection], attribute)
        if data_is_collection:
            data = [e.value for e in data]
        yield action_steps.UpdateProgress(
            text='Got data', detail=data
        )

get_data_name = test_context.bind(('get_data',), GetData())

class SetData(Action):

    def model_run(self, model_context, mode):
        row, attribute, value = mode
        element = model_context.proxy.get_model()[row]
        setattr(element, attribute, value)
        yield action_steps.UpdateObjects((element,))
        yield action_steps.UpdateProgress(text='Data set')

set_data_name = test_context.bind(('set_data',), SetData())

class AddZ(Action):

    def model_run(self, model_context, mode):
        new_c = C(1)
        collection = model_context.proxy.get_model()
        collection[0].z.append(new_c)
        yield action_steps.CreateObjects((new_c,))

add_z_name = test_context.bind(('add_z',), AddZ())

class RemoveZ(Action):

    def model_run(self, model_context, mode):
        collection = model_context.proxy.get_model()
        old_c = collection[0].z.pop()
        yield action_steps.DeleteObjects((old_c,))

remove_z_name = test_context.bind(('remove_z',), RemoveZ())

class SwapElements(Action):

    def model_run(self, model_context, mode):
        collection = model_context.proxy.get_model()
        collection[0:2] = [collection[1], collection[0]]
        yield action_steps.UpdateProgress(text='Elements swapped')

swap_elements_name = test_context.bind(('swap_elements',), SwapElements())

class AddElement(Action):

    def model_run(self, model_context, mode):
        new_a = A(mode)
        collection = model_context.proxy.get_model()
        collection.append(new_a)
        yield action_steps.CreateObjects((new_a,))

add_element_name = test_context.bind(('add_element',), AddElement())

class RemoveElement(Action):

    def model_run(self, model_context, mode):
        collection = model_context.proxy.get_model()
        last_element = collection[-1]
        # emitting the deleted signal happens before the object is
        # deleted        
        yield action_steps.DeleteObjects((last_element,))
        # but removing an object should go through the item_model or there is no
        # way the item_model can be aware.        
        model_context.proxy.remove(last_element)
        yield action_steps.UpdateProgress(text='Element removed')

remove_element_name = test_context.bind(('remove_element',), RemoveElement())

class GetCollection(Action):

    def model_run(self, model_context, mode):
        name = initial_naming_context._bind_object((object(),))
        yield action_steps.UpdateProgress(
            text='Got data', detail=name
        )

get_collection_name = test_context.bind(('get_collection',), GetCollection())


class SetupQueryProxy(Action):

    def __init__(self, admin_cls):
        self.admin_cls = admin_cls

    def model_run(self, model_context, mode):
        session = Session()
        admin = self.admin_cls(app_admin, Person)
        proxy = QueryModelProxy(session.query(Person))
        model_context = ObjectsModelContext(admin, proxy, QtCore.QLocale())
        initial_naming_context.rebind(tuple(mode), model_context)
        yield action_steps.UpdateProgress(detail='Proxy setup')

setup_query_proxy_name = test_context.bind(('setup_query_proxy',), SetupQueryProxy(admin_cls=Person.Admin))

class EqualColumnAdmin(Person.Admin):
    list_display = ['first_name', 'last_name']
    # begin column width
    field_attributes = {
        'first_name':{'column_width':8},
        'last_name':{'column_width':8},
    }
    # end column width

setup_query_proxy_equal_columns_name = test_context.bind(('setup_query_proxy_equal_columns',), SetupQueryProxy(admin_cls=EqualColumnAdmin))

class SmallColumnsAdmin( Person.Admin ):
    list_display = ['first_name', 'last_name']

setup_query_proxy_small_columns_name = test_context.bind(('setup_query_proxy_small_columns',), SetupQueryProxy(admin_cls=SmallColumnsAdmin))

class ApplyFilter(Action):

    def model_run(self, model_context, mode):

        class SingleItemFilter(list_filter.Filter):
        
            def decorate_query(self, query, values):
                return query.filter_by(id=values)

        model_context.proxy.filter(SingleItemFilter(Person.id), 1)
        yield action_steps.UpdateProgress(detail='Filter applied')

apply_filter_name = test_context.bind(('apply_filter',), ApplyFilter())

class InsertObject(Action):


    def model_run(self, model_context, persons_name):
        person = Person()
        count = len(model_context.proxy)
        model_context.proxy.append(person)
        assert model_context.proxy.index(person)==count
        yield action_steps.CreateObjects((person,))
        yield action_steps.UpdateProgress(text='Object inserted', detail=id(person))

insert_object_name = test_context.bind(('insert_object',), InsertObject())

class GetEntityData(Action):

    def model_run(self, model_context, mode):
        primary_key, attribute = mode
        entity = model_context.session.query(Person).get(primary_key)
        data = getattr(entity, attribute)
        yield action_steps.UpdateProgress(
            text='Got enity data', detail=data
        )

get_entity_data_name = test_context.bind(('get_entity_data',), GetEntityData())

class StartQueryCounter(Action):

    @staticmethod
    def increase_query_counter(conn, cursor, statement, parameters, context, executemany):
        current_count = test_context.resolve(('current_query_count',))
        current_count = current_count + 1
        LOGGER.debug('Counted query {} : {}'.format(
            current_count, str(statement)
        ))
        test_context.rebind(('current_query_count',), current_count)

    def model_run(self, model_context, mode):
        test_context.rebind(('current_query_count',), 0)
        event.listen(Engine, 'after_cursor_execute', self.increase_query_counter)
        yield action_steps.UpdateProgress(text='Started query counter')

test_context.bind(('current_query_count',), 0)
start_query_counter_name = test_context.bind(('start_query_counter',), StartQueryCounter())

class StopQueryCounter(Action):

    def model_run(self, model_context, mode):
        current_count = test_context.resolve(('current_query_count',))
        event.remove(Engine, 'after_cursor_execute', StartQueryCounter.increase_query_counter)
        yield action_steps.UpdateProgress(
            text='Stopped query counter', detail=current_count
        )

stop_query_counter_name = test_context.bind(('stop_query_counter',), StopQueryCounter())


class SetupSampleModel(Action):

    @classmethod
    def setup_sample_model(cls):
        metadata.bind = model_engine
        metadata.drop_all(model_engine)
        metadata.create_all(model_engine)
        cls.session = Session()
        cls.session.expunge_all()
        return model_engine

    def model_run(self, model_context, mode):
        self.setup_sample_model()
        yield action_steps.UpdateProgress(detail='Model set up')

setup_sample_model_name = unit_test_context.bind(('setup_sample_model',), SetupSampleModel())

class LoadSampleData(Action):

    def model_run(self, model_context, mode):
        if mode in (None, True):
            load_movie_fixtures(model_engine)
            yield action_steps.UpdateProgress(detail="samples loaded")

load_sample_data_name = unit_test_context.bind(('load_sample_data',), LoadSampleData())

class SetupSession(Action):

    def model_run(self, model_context, mode):
        session = Session()
        session.close()
        yield action_steps.UpdateProgress(detail='Session closed')

setup_session_name = unit_test_context.bind(('setup_session',), SetupSession())

class DirtySession(Action):
    
    def model_run(self, model_context, mode):
        session = Session()
        session.expunge_all()
        # create objects in various states
        #
        p2 = Person(first_name = u'p2', last_name = u'dirty' )
        p3 = Person(first_name = u'p3', last_name = u'deleted' )
        p4 = Person(first_name = u'p4', last_name = u'to be deleted' )
        p6 = Person(first_name = u'p6', last_name = u'deleted outside session' )
        session.flush()
        p3.delete()
        session.flush()
        p4.delete()
        p2.last_name = u'clean'
        #
        # delete p6 without the session being aware
        #
        person_table = Person.table
        session.execute(
            person_table.delete().where( person_table.c.id == p6.id )
        )
        yield action_steps.UpdateProgress(detail='Session dirty')

dirty_session_action_name = unit_test_context.bind(('dirty_session',), DirtySession())

class CustomAction(Action):
    name = 'custom_test_action'
    verbose_name = 'Custom Action'
    shortcut = QtGui.QKeySequence.StandardKey.New
    modes = [
        Mode('mode_1', _('First mode')),
        Mode('mode_2', _('Second mode')),
    ]


custom_action_name = test_context.bind((CustomAction.name,), CustomAction())

group_box_filter_name = unit_test_context.bind(('group_box',), list_filter.GroupBoxFilter(Person.last_name, exclusive=True))
combo_box_filter_name = unit_test_context.bind(('combo_box',), list_filter.ComboBoxFilter(Person.last_name))
to_first_row_name = unit_test_context.bind(('to_first_row',), list_action.ToFirstRow())
to_last_row_name = unit_test_context.bind(('to_last_row',), list_action.ToLastRow())
export_spreadsheet_name = unit_test_context.bind(('export_spreadsheet',), list_action.ExportSpreadsheet())
import_from_file_name = unit_test_context.bind(('import_from_file',), list_action.ImportFromFile())
set_filters_name = unit_test_context.bind(('set_filters',), list_action.SetFilters())
open_form_view_name = unit_test_context.bind(('open_form_view',), list_action.OpenFormView())
remove_selection_name = unit_test_context.bind(('remove_selection',), list_action.RemoveSelection())
close_form_name = unit_test_context.bind(('close_form',), form_action.CloseForm())
backup_action_name = unit_test_context.bind(('backup',), application_action.Backup())
restore_action_name = unit_test_context.bind(('restore',), application_action.Restore())
change_logging_action_name = unit_test_context.bind(('change_logging',), ChangeLogging())
segmentation_fault_action_name = unit_test_context.bind(('segmentation_fault',), application_action.SegmentationFault())
refresh_action_name = unit_test_context.bind(('refresh',), application_action.Refresh())

class ModelContextAction(Action):
    name = 'model_context_action'
    verbose_name = 'Model context methods'

    def model_run(model_context, mode):
        for obj in model_context.get_collection():
            yield action_steps.UpdateProgress('obj in collection {}'.format(obj))
        for obj in model_context.get_selection():
            yield action_steps.UpdateProgress('obj in selection {}'.format(obj))
        model_context.get_object()

model_context_action_name = test_context.bind((ModelContextAction.name,), ModelContextAction())

class SendDocumentAction( Action ):

    def model_run( self, model_context, mode ):
        methods = [
            CompletionValue(
                initial_naming_context._bind_object('email'),
                'By E-mail'),
            CompletionValue(
                initial_naming_context._bind_object('email'),
                'By Fax'),
            CompletionValue(
                initial_naming_context._bind_object('email'),
                'By postal mail')
        ]
        method = yield action_steps.SelectItem(
            methods,
            value=initial_naming_context._bind_object('email')
        )
        LOGGER.info('selected {}'.format(method))

send_document_action_name = unit_test_context.bind(('send_document_action',), SendDocumentAction())

class CancelableAction(Action):

    iterations = 10
    steptime = 3 # every <steptime> seconds

    def model_run(self, model_context, mode):
        timer = QtCore.QElapsedTimer()
        timer.start()
        for i in range(self.iterations):
            time.sleep(self.steptime)
            yield action_steps.UpdateProgress(i, self.iterations)

cancelable_action_name = unit_test_context.bind(('cancelable_action',), CancelableAction())

class MainAction(Action):

    def model_run(self, model_context, mode):
        yield action_steps.UpdateProgress(1,1)


initial_naming_context.bind('test', test_context)
initial_naming_context.rebind('main', MainAction())
engine = SetupSampleModel.setup_sample_model()
load_movie_fixtures(engine)

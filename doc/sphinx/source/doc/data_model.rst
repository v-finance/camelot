.. _doc-data_model:

########################
  Built in data models
########################

Camelot comes with a number of built in data models.  To avoid boiler plate models needed in almost any application (like Persons, Addresses, etc.), 
the developer is encouraged to use these data models as a start for developing custom applications.   

Modules
=======

The :mod:`camelot.model` module contains a number of submodules, each with a specific purpose

To activate such a submodule, the submodule should be imported in the `setup_model` method of `settings` class,
before the tables are created ::

   def setup_model( self ):
       from camelot.core.sql import metadata
       metadata.bind = self.ENGINE()
       from camelot.model import authentication
       from camelot.model import party
       from camelot.model import i18n
       from camelot.core.orm import setup_all
       setup_all( create_tables=True ) 
       
.. _model-persons:

Persons and Organizations
-------------------------

.. automodule:: camelot.model.party
   :members:

I18N
----

.. automodule:: camelot.model.i18n
   :members:

Fixture
-------

.. automodule:: camelot.model.fixture
   :members:

Authentication
--------------

.. automodule:: camelot.model.authentication
   :members:
   
Batch Jobs
----------

.. automodule:: camelot.model.batch_job
   :members:

A batch job object can be used as a context manager :

.. literalinclude:: ../../../../test/test_model.py
   :start-after: begin batch job example
   :end-before: end batch job example

Whenever an exception happens inside the `with` block, the stack trace
of this exception will be written to the bach job object and it's status will
be set to `errors`.  At the end of the `with` block, the status of the
batch job will be set to `finished`.

History tracking
----------------

.. automodule:: camelot.model.memento
   :members:

Customization
=============

Adding fields
-------------

Sometimes the built in models don't have all the fields or relations required for a specific application.
Fortunately it is possible to add fields to an existing model on a per application base.

To do so, simply assign the required fields in the application specific model definition,
before the tables are created.

.. literalinclude:: ../../../../test/test_model.py
   :start-after: begin add custom field
   :end-before: end add custom field

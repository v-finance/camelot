.. _doc-data_model:

########################
  Built in data models
########################

Camelot comes with a number of built in data models.  To avoid boiler platem odels needed in almost any application (like Persons, Addresses, etc.), 
the developer is encouraged to use these data models as a start for developing custom applications.

To activate a model, the model should be imported in the `setup_model` method of `settings.py`::

   def setup_model():
       from camelot.core.sql import metadata
       metadata.bind = ENGINE()
       from camelot.model import authentication
       from camelot.model import party
       from camelot.model import i18n
       from elixir import setup_all
       setup_all( create_tables=True )    

Some of these models are still developed using `Elixir`, therefor, when using these models the `setup_all` method should be called in `settings.py` to activate
the `Elixir` mapping.  This is not needed when only `Declarative` model definitions are used.

.. _model-persons:

Persons and Organizations
=========================

.. automodule:: camelot.model.party
   :members:

I18N
====

.. automodule:: camelot.model.i18n
   :members:

Fixture
=======

.. automodule:: camelot.model.fixture
   :members:

Authentication
==============

.. automodule:: camelot.model.authentication
   :members:
   
Batch Jobs
==========

.. automodule:: camelot.model.batch_job
   :members:

History tracking
================

.. automodule:: camelot.model.memento
   :members:

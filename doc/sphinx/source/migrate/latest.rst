.. _migrate-latest:

Migrate from Camelot 13.04.13 to the development branch
=======================================================

 * Database migration commands for the changed authentication model::

      ALTER TABLE authentication_mechanism ADD COLUMN representation character varying;

 * In custom validators, the `objectValidity` method should be renamed to
   `validate_object`

 * The `SelectObject` action step has been removed, its use should be replaced
   with the `SelectObjects` action step 

 * In the default party model, all relations between parties have been removed
   (such as Employer, Employee, Customer, Supplier).  If these are needed in 
   an application, they should be added in the application itself.
 
 * The `SelectFile` action step can no longer be used to select a non existing
   file, use `SaveFile` instead.

.. _migrate-latest:

Migrate from Camelot 13.04.13 to the development branch
=======================================================
   
 * Database migration commands for the changed authentication model::
 
      ALTER TABLE authentication_mechanism ADD COLUMN representation character varying;
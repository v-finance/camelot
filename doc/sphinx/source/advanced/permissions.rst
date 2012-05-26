.. _doc-permissions:

################################
  Authentication and permissions
################################

fine grained authentication and authorization is not yet included as part of the Camelot framework.

what is included is the function :

:func:`camelot.model.authentication.get_current_authentication`

which returns an object of type :class:`camelot.model.authentication.AuthenticationMechanism

where the username is the username of the currently logged in user (because on most desktop
apps, you don't want a separate login process for your app, but rely on that of the OS).

this function can then be used if you build the `Admin` classes for your application :

 * set the *editable* field attribute to a function that only
   returns Thrue when the current authentication requires
   editing of fields
   
 * in the `ApplicationAdmin.get_sections method`, to hide/show
   sections depending on the logged in user

 * in the `EntityAdmin` subclasses, in the `get_field_attributes`
   method, to set fields to editable=False/True depending on
   the logged in user 


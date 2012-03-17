.. _doc-faq:

###########################
 Frequently Asked Questions
###########################

How to use the PySide bindings instead of PyQt ?
------------------------------------------------

The Camelot sources as well as the example videostore application can be
converted from PyQt applications to PySide with the `camelot_admin` tool.

Download the sources and position the shell in the main directory, and then
issue these commands::

    python camelot/bin/camelot_admin.py to_pyside .
    
This will create a subdirectory 'to_pyside' which contains the converted
source code.

Why is there no :guilabel:`Save` button ?
-----------------------------------------

Early on in the development process, the controversial decision was made not
to have a :guilabel:`Save` button in Camelot. Why was that ?

  - User friendlyness.  One of the major objectives of Camelot is to be
    user friendly.  This also means we should reduce the number of 'clicks'
    a user has to do before achieving something.  We believe the 'Save' click
    is an unneeded click.  The application knows when the state of a form is
    valid for persisting it to the database, and can do so without user
    involvement.  We also want to take the 'saving' issue out of the mind
    of the user, he should not bother wether his work is 'saved', it simply is.
    
  - Technical.  Once you decide to use a :guilabel:`Save` button, you need to
    ask yourself where you will put that button and what its effect will be. 
    This question becomes difficult when you want to enable the user to edit
    a complex datastructure with one-to-many and many-to-many relations.  Most
    applications solve this by limiting the options for the user.  For example,
    most accounting packages will not allow you to create a new customer when 
    you are creating a new invoice.  Because when you save the invoice, should
    the customer be saved as well ?  Or should the customer have it's own save
    button ?  Those packages therefor require the user to first create a
    customer, and only then can an invoice be created.  These are limitation we
    don't want to impose with Camelot.
    
  - Consistency between editing in table or form view.  We wanted the table
    view to be really easy to edit (to behave a bit like a spreadsheet), so it's
    easy for the user to do bulk updates.  As such the user should not be
    bothered by pressing the :guilabel:`Save` button all the time.  If there is
    no need to save in the table view, there should be no need in the form view
    either.
    
Some couter arguments for this decision are :

  - But what if the user wants to 'modify' a form and not save those changes ?
    This is indeed something that is not possible without a :guilabel:`Save` and
    it accompanying :guilabel:`Cancel` button.  But this is something a developer
    will do a lot while testing an application, but is outside of the normal
    workflow of a user.  Most users typically want to enter or modify as much
    data as possible, they are not testing the application to see how it would
    behave on certain data input.
    
  - A form should be validated before it is saved.  In an application there are
    two levels of validation.  The first level is to validate before something
    is persisted into the database, this can be done in Camelot using a custom
    implementation of a 
    :class:`camelot.admin.validator.entity_validator.EntityValidator`.  The
    second level is a validation before the entered data can be used in the
    business process.  To do this second level validation, one can use state
    changes (Action buttons that change the state of a form, eg from 'Draft'
    to 'Complete').  A good example of this is when entering a booking into 
    an accounting package.  When a booking is entered, it can only be used when
    debit equals credit.  What would happen when this validation is done at the
    moment the form is 'saved'.  Suppose a user has been working for the better
    part of the day on a complex booking, but is not done yet at the end of
    the day.  Since he cannot yet save his work he has two options, discard it
    and restart the next day, or enter some bogus data to be able to save it.
    What will happen in the later case when his manager is creating a report
    a bit later.  So the correct situation in this case is having your work
    saved at all times, and to put your booking from a 'draft' state to a
    'complete' state once its ready.  This state change will then check if
    debit equals credit.

Two years after we made this move, Apple decided to follow our
example : http://www.apple.com/macosx/whats-new/auto-save.html

But my users really want a :guilabel:`Save` button ?
----------------------------------------------------

We advise you to listen very well to the arguments the user has for wanting
a :guilabel:`Save` button.  You will be able to solve most of them by using
state changes instead of a :guilabel:`Save` button.  The other arguments 
probably have to do with expections users have from using other applications,
as for those simply ask the users to try to work for a week without a 
:guilabel:`Save` button and get back to you if after that week, they still
have issues with it.  Please let us know when they do !

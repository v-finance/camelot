.. _doc-documents:

#######################
  Document Management
#######################

Camelot provides some features for the management of documents.  Notice that
documents managed by Camelot are stored in a specific location (either an
application directory on the local disk, a network share or a remote server).

This in contrast with some application that just store the link to a file in
the database, and don't store the file itself.

Three concepts are important for understanding how Camelot handles documents :

    * The **Storage** : this is the place where Camelot stores its documents,
      by default this is a directory on the local system.  When a file is
      checked in into a storage, a StoredFile is returned.  Files are checked
      out from the storage by their StoredFile representation.
      
    * The **StoredFile** : a stored file is a representation of a file stored
      in a storage.  It does not contain the file itself but its name and meta
      information.
      
    * The **File** Field type : is a custom field type to write and read the
      StoredFile into the database.  The actual name of the StoredFile is the
      only thing stored in the database.
      
The File field type
===================

Usually the first step when working with documents is to use the File field
type somewhere in the model definition.  Alternatively the Image field type
can be used if one only wants to store images in that field.

.. autoclass:: camelot.types.File

.. autoclass:: camelot.types.Image

The StoredFile
==============

When the File field type is used in the code, it returns and accepts objects of
type StoredFile.


.. autoclass:: camelot.core.files.storage.StoredFile
   :members:

The Image field type will return objects of type StoredImage.

.. autoclass:: camelot.core.files.storage.StoredImage
   :members:

The Storage
===========

This is where the actual file is stored.  The default storage implementation
simply represents a directory on the file system.

.. autoclass:: camelot.core.files.storage.Storage
   :members:
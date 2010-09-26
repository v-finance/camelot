.. _doc-charts:

##########
  Charts
##########

:Release: |version|
:Date: |today|

To enable charts, **Camelot** is closely integrate with `Matplotlib <http://www.matplotlib.org>`_,
one of the very high quality Python charting packages.

Often creating a chart involves gathering a lot of data, this needs to happen inside the model, to
free the GUI from such tasks.  Once the data is gathered, it is put into a container, this container
is then shipped to the gui thread, where the chart is put on the screen.

.. image:: ../_static/editors/ChartEditor_editable.png

A simple plot
=============

As shown in the example below, creating a simple plot involves two things :

  1. Create a property that returns one of the chart containers, in this case
     the **PlotContainer** is used.
     
  2. Specifiy the delegate to be used to visualise the property, this should be
     the **ChartDelegate**
     
.. literalinclude:: ../../../../test/snippet/chart/simple_plot.py
  
The **PlotContainer** object takes as its arguments, the same arguments that can be passed to the
matplotlib plot command.  The container stores all those arguments, and later passes them to the
plot command executed within the gui thread.

.. image:: ../_static/snippets/simple_plot.png

Chart containers
================

.. automodule:: camelot.container.chartcontainer
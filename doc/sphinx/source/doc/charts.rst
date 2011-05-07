.. _doc-charts:

##########
  Charts
##########

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
     
  2. Specify the delegate to be used to visualize the property, this should be
     the **ChartDelegate**
     
.. literalinclude:: ../../../../test/snippet/chart/simple_plot.py
  
The **PlotContainer** object takes as its arguments, the same arguments that can be passed to the
matplotlib plot command.  The container stores all those arguments, and later passes them to the
plot command executed within the gui thread.

.. image:: ../_static/snippets/simple_plot.png

The simpel chart containers map to their respective matplotlib command.  They include :

.. autoclass:: camelot.container.chartcontainer.PlotContainer

.. autoclass:: camelot.container.chartcontainer.BarContainer

Advanced Plots
==============

For more advanced plots, the **AxesContainer** class can be used.  The AxesContainer class can be
used as if it were a matplotlib Axes object.  But when a method on the AxesContainer is called it
will record the method call instead of creating a plot.  These method calls will then be replayed
by the gui to create the actual plot.

.. literalinclude:: ../../../../test/snippet/chart/advanced_plot.py

.. image:: ../_static/snippets/advanced_plot.png

More
====

For more information on the various types of plots that can be created, have a look at the 
`Matplotlib Gallery <http://matplotlib.sourceforge.net/gallery.html>`_.

When the AxesContainer does not provide enough flexibility, for example when the plot needs to
manipulated through its object structure, more customization is possible by subclassing either
the AxesContainer or the FigureContainer :

.. autoclass:: camelot.container.chartcontainer.AxesContainer
  :members:

.. autoclass:: camelot.container.chartcontainer.FigureContainer
  :members:
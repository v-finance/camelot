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

Chart containers
================

.. automodule:: camelot.container.chartcontainer
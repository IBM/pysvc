Installing / Upgrading
======================
.. highlight:: bash


**pysvc** is in the `Python Package Index
<http://pypi.python.org/pypi/pysvc/>`_.

Installing with pip
-------------------

We prefer `pip <http://pypi.python.org/pypi/pip>`_
to install **pysvc** on platforms other than Windows::

  $ pip install pysvc

To upgrade using pip::

  $ pip install --upgrade pysvc

Installing with easy_install
----------------------------

If you must install pysvc using
`setuptools <http://pypi.python.org/pypi/setuptools>`_ do::

  $ easy_install pysvc

To upgrade do::

  $ easy_install -U pysvc


Installing from source
----------------------

If you'd rather install directly from the source (i.e. to stay on the
bleeding edge), then check out the latest source from github and 
install the driver from the resulting tree::

  $ git clone https://github.com/ibm/pysvc.git
  $ cd pysvc
  $ pip install .

Uninstalling an old client
--------------------------

If the older **pysvc** was installed on the system already it
will need to be removed. Run the following command to remove it::

  $ sudo pip uninstall pysvc

===========
SFTP Access
===========

SFTP is a secure and convenient way to access, browse and download large Experiments,
Datasets and Files from MyTardis.

In order to access data on MyTardis via SFTP, you will first need to install an
SFTP client. There are many free and commercial SFTP clients for you to choose
from; however, we recommend `Cyberduck (Win & Mac) <https://cyberduck.io>`_,
`FileZilla (All platforms) <https://filezilla-project.org/>`_ or `WinSCP (Win
only) <https://winscp.net/eng/index.php>`_ for the majority of users. The
instructions here will focus on `Cyberduck (Win & Mac) <https://cyberduck.io>`_.

Browse and Download your MyTardis data using SFTP
-------------------------------------------------
1. Open your SFTP client and create a new connection with the following configuration:
  +-------------+-----------------------------------------+
  | Parameter   | Value                                   |
  +=============+=========================================+
  | Server:     | *URL for your MyTardis deployment*      |
  |             | e.g. `<https://store.erc.monash.edu>`_  |
  +-------------+-----------------------------------------+
  | Port:       | 2200                                    |
  +-------------+-----------------------------------------+
  | Username:   | *Your MyTardis username*                |
  +-------------+-----------------------------------------+
  | Password:   | *Your MyTardis password*                |
  +-------------+-----------------------------------------+
  Note: you should substitute your MyTardis details for *italicised* values.

.. image:: ../images/userguide/cyberd_open_conn.png

2. Click **Connect**
3. Upon successful connection you will be presented with a file browser
   showing all your data on MyTardis.

Data is organised according to the Experiment/Dataset/Data File hierarchy/structure described in the :ref:`org_data`
section.


Browse and/or Download a Specific Experiment or Dataset
-------------------------------------------------------
MyTardis also provides a convenient way to access/browse a particular Experiment or Dataset via SFTP.

1. Navigate to the Experiment or Dataset page that you want to access via SFTP
   using your web browser.
#. There is an **SFTP** button in the *Download* section on both the Experiment
   and Dataset views.

.. image:: ../images/userguide/sftp_buttons.png

3. Clicking the **SFTP** button at either of these two locations will redirect you
   to a page with instructions and links for starting an SFTP session for a
   specific experiment or dataset.

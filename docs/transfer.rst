====
Transfer App
====

The transfer app oversees the transfer and synchronisation of experiments between providers (e.g. The Synchrotron) and consumers (e.g. Home institutions such as Monash). The app has a provider component and a consumer component, to be deployed at the respective locations, that define a protocol allowing:

* A provider to notify consumers of new experiments, and register them with the consumer
* A consumer to request the transfer data files for experiments from a provider
* A consumer to poll the provider for status of a transfer of data files

The consumer also manages the state of each experiment, so success or failure of the transfer can be easily determined on the consumer side. Failed transfers log data about the cause of the failure and can be restarted with user intervention.

Common Setup
============

Add the sync application and dependencies to the INSTALLED_APPS list in your MyTardis project's settings file. The transfer app overrides a number of templates in the tardis_portal app, and so should be above it in the INSTALLED_APPS list.

.. code-block:: python

    INSTALLED_APPS += (
        TARDIS_APP_ROOT + '.sync',
    )

Set the base URL of this MyTardis instance::

    MYTARDIS_SITE_URL = 'https://mytardis.schoolofhardknocks.com'

Set the list of email addresses that will receive admin notifications about experiment transfer success and failure::

    SYNC_ADMINS = ('tardis-admin@schoolofhardknocks.com',)

Consumer Setup
==============

Apply the settings from `Common Setup`.

The consumer side of the app requires django-celery. This will periodically check all of your experiments to see if any action is needed, like requesting a file transfer or verifying data integrity.

The default configuration of tardis already has django-celery configured in the settings file. Confirm that the dependencies are added to the INSTALLED_APPS list in your MyTardis project's settings file. You will also need to add a task to run the transfer apps clock_tick task as shown below.

.. code-block:: python

    import djcelery

    INSTALLED_APPS += (
        'djcelery',
        'djkombu',
    )

    CELERYBEAT_SCHEDULE = {
        "tasks.clock": {
            "task": "tardis.apps.sync.tasks.clock_tick",
             "schedule": timedelta(seconds=30)
        },
    }
    djcelery.setup_loader()

Set the pre-shared key that allows this MyTardis instance to request file transfers and status updates from the upstream institution (the institution running the provider should have given you this)::

    SYNC_CLIENT_KEY = 'abcdefghijklmnopqrstuvwxyz0123456789'

Run syncdb to add the SyncedExperiment table to the database. The app does not alter any existing tables so there is no need to do a migrate.

If you are setting up a consumer, start celery and celerybeat together by switching to your MyTardis checkout and running::

    $ ./bin/django celeryd -B

This will start a clock which periodically checks your experiments and attempts to progress any that haven't been completely transferred to your home institution.

.. warning::

    The sync app currently requires that the celery process concurrency be set to 1, so only one instance of the task is running at a time. This will be fixed in a later release.

Provider Setup
==============

Apply the settings from `Common Setup`.

Additionally, define a list of (IP, key) pairs that define which MyTardis consumers are able to access the provider views::

    SYNC_CLIENT_KEYS = (
        ('127.0.0.1', 'abcdefghijklmnopqrstuvwxyz0123456789'),
    )

And set the manager that the sync manager will use. Set it to the default for now::

    SYNC_MANAGER_CLASS = 'managers.default_manager.SyncManager'

.. note::

    This manager does nothing by default. You will need to extend it to support your specific transfer method.

Settings
=====

Celery
------
Celery runs the tasks that periodically check to see if there are any experiments that haven't been properly transferred to the home institution it is running at, and attempts to progress those experiments down the transfer workflow.

The main setting you'll be interested in here is the "Schedule" value in the CELERYBEAT_SCHEDULE dictionary. Set this to the frequency that you'd like celery to check for new experiments.

SYNC_MANAGER
------------

The transfer app comes with a number of default implementations of parts of its backend. These can be replaced in order to addapt the transfer app to work with the backends at your particular institution.

The SyncManager class defines the interface for the backends at a provider that the rest of the app (Read: the views) plugs into.

The app comes with a default implementation of a SyncManager, the DefaultManager. Specify this in your settings if you're happy to use the default implementation.::

    SYNC_MANAGER = 'managers.default_manager'

The default manager uses the following:

* The default www.tardis.edu.au registry of sites to find sites to receive information about experiments
* A format of 'tardis.<EPN>' to generate the UIDs used by the sync manager to identify experiments across institutions
* METS export to send experiment data
* Has the file transfer method (to send files for experiments) stubbed and will need to be defined if you want to send files (i.e. if your deployment is a provider).
* Has the status request method stubbed (will always return a failure message on being queried)

To make the DefaultManager do something more useful, you will need to extend the class.

Architecture
============

The sync app consists of two components or sub-apps; The consumer sub-app and the provider sub-app. They are presented in the one app (rather than two separate apps) to aid understandability, and also as there is a considerable shared amount of code between the two.

Each sub-app has an interface which defines how its counterpart can query it and post data to it. Each sub-app has a number of pluggable components which can be replaced (either through changing the settings file or subclassing the components) on a deployment by deployment basis, to reflect the different backends of each MyTardis employment (e.g. different site registries, different file transfer methods).

Consumer
--------

The consumer handles the registration of new experiments from a provider, initiates data transfer of datafiles from the providing institution, and keeps track of the progress of these transfers. Should a transfer fail, the consumer sets the state of a transfer to 'failed permanent' and the appropriate user is notified.


Models
~~~~~~

SyncedExperiment
    This is the only model added by the sync app. The model links an existing tardis.tardis_portal.Experiment model to information about the state of the transfer of the experiment to the home institution.

    A ``SyncedExperiment`` object is created when the app receives the ``remote_received`` signal from the tardis_portal app. These objects are only created on the consumer side (i.e. deployments of MyTardis that receive experiments from other deployments) and only if they have been received from another origin (Experiments created locally will not be wrapped).

    The ``SyncedExperiment`` model tracks progress after the experiment is initially ingested into the home institution. This is done using a custom django field 'FSMField'. The field stores the state of a finite state machine (FSM), which tells us at any time what state the transfer is in. Each state in the FSM is defined as its own class, and defines a method ``get_next_state`` which can be called to progress to the next state. Each state defines a list operations to attempt to perform for that state, and conditions to progress to subsequent states. The app comes with a default FSM which reflects a regular transfer workflow, but can be changed or extended by adding classes that subclass the State class.

    The default deployment of the sync app uses Celery (specifically, celerybeat) to periodically get a list of all SyncedExperiments that are not in the COMPLETE state, and attempts to progress them to their next state. The steps for setting up Celery are outlined in the Setup section of this document.

Components
~~~~~~~~~~

TransferClient
    Defines the consumer side of the communication protocol between the consumer and the provider. Generally, this component will be the same for most deployments and should not need to be altered. The TransferClient class is called by the consumer state machine to progress the state of the SyncedExperiment.

    ``request_file_transfer(synced_experiment)`` makes a request to the provider to begin the transfer of the files for the SyncedExperiment synced_experiment. This makes a HTTP request to the provider app running on the upstream MyTardis. The SyncManager implementation on the provider side will handle this request and start a file transfer between the file servers of the two institutions.

    ``get_status(synced_experiment)`` If the files for an experiment are in the process of being transferred to the home institution, this function may be used to query the progress of the transfer from the providing institution.

Provider
--------

Views
~~~~~
*get_experiment*

*transfer_status*

Models
~~~~~~
None

Components
~~~~~~~~~~

*TransferService*

Think of this as the counterpart to the TransferClient on the consumer side. This is a very shallow wrapper that defines an interface and uses a user-specified instance of a SyncManager as the backend. The TransferService class is called to take action on requests received through the provider views.

*SyncManager*

To override the implementation of the default SyncManager provider, a developer should inherit from SyncManager and re-implement the appropriate functions.

*SiteManager*

Manages the retrieval of information about home institutions that will need experiments. By default, this retrieves a list of sites, as well as their configurations from www.tardis.edu.au.

Admin
=====

(Synchrotron-specific) The app adds a 'transfer' command to the admin interface to which an experiment EPN can be passed. If the deployment is a provider, it will attempt to broadcast the experiment denoted by the EPN to all registered sites.


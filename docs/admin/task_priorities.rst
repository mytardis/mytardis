Task Priorities
===============

Overview
--------

From v4.1.0, MyTardis assumes the use of RabbitMQ as its message broker,
and instructs Celery to create a "celery" queue with task priorites
enabled.  The queue's maximum priority is set to 10 in
``tardis/default_settings/celery_settings.py`` which is used when setting up
the Celery app in ``tardis/celery.py``::

  tardis/default_settings/celery_settings.py
  ------------------------------------------
  ...
  MAX_TASK_PRIORITY = 10
  DEFAULT_TASK_PRIORITY = 5
  DEFAULT_EMAIL_TASK_PRIORITY = 10
  
  task_default_queue = 'celery'
  # The 'x-max-priority' argument will only be respected by the RabbitMQ broker,
  # which is the recommended broker for MyTardis:
  task_queues = (
      Queue('celery', Exchange('celery'),
            routing_key='celery',
            queue_arguments={'x-max-priority': MAX_TASK_PRIORITY}),
  )

  tardis/celery.py
  ----------------
  ...
  tardis_app = Celery('tardis')
  tardis_app.config_from_object('django.conf:settings')
  ...

Celery's ``apply_async`` method's ``shadow`` argument is used to annotate storage
box related task names with the location (storage box name) which they are
running in, e.g. ``dfo_verify`` becomes ``dfo_verify location:default-storage``::

  tardis/tardis_portal/tasks.py
  -----------------------------
  ...
  def verify_dfos(**kwargs):
      ...
      for dfo in dfos_to_verify:
          kwargs['priority'] = dfo.priority
          kwargs['shadow'] = 'dfo_verify location:%s' % dfo.storage_box.name
          dfo_verify.apply_async(args=[dfo.id], **kwargs)
  ...


Monitoring
----------

We can confirm that the ``x-max-priority`` argument was supplied when creating the
queue by running ``rabbitmqctl report`` on our RabbitMQ server::

  $ sudo rabbitmqctl report | grep 'x-max-priority'
  ...
  Listing queues for vhost mytardis ...
  name    durable auto_delete     arguments ...
  ...
  celery	true	false	[{"x-max-priority",10}] ...

We can list the tasks currently running (and observe their priorities) by
running ``celery inspect active`` from one of our Celery nodes::

  (mytardis) mytardis@celery0 ~/mytardis$ DJANGO_SETTINGS_MODULE=tardis.settings celery -A tardis.celery.tardis_app inspect active
  -> celery@allqueues.celery0: OK
      * {u'args': u'[32933203]', u'time_start': 1548368931.7151582, u'name': u'dfo_verify location:default-storage',
         u'delivery_info': {u'priority': 5, u'redelivered': False, u'routing_key': u'celery', u'exchange': u''},
         u'hostname': u'celery@allqueues.celery0', u'acknowledged': False, u'kwargs': u'{}',
         u'type': u'tardis_portal.dfo.verify', u'id': u'50c80b84-5d64-44c7-a6d4-c551b6d14e22', u'worker_pid': 3730}
  -> celery@allqueues.celery2: OK
      - empty -
  ...
  -> celery@allqueues.celery7: OK
      * {u'args': u'[30476811]', u'time_start': 1548368924.2799926, u'name': u'dfo_verify location:default-storage',
         u'delivery_info': {u'priority': 5, u'redelivered': False, u'routing_key': u'celery', u'exchange': u''},
         u'hostname': u'celery@allqueues.celery7', u'acknowledged': False, u'kwargs': u'{}',
         u'type': u'tardis_portal.dfo.verify', u'id': u'de7d0fe1-f386-4937-af7f-a693e7630fb5', u'worker_pid': 9051}
  ...
  -> celery@allqueues.celery14: OK
      * {u'args': u'[289]', u'time_start': 1548368427.9639463, u'name': u'sbox_cache_files location:big-data1',
         u'delivery_info': {u'priority': 4, u'redelivered': False, u'routing_key': u'celery', u'exchange': u''},
         u'hostname': u'celery@allqueues.celery14', u'acknowledged': False, u'kwargs': u'{}',
         u'type': u'tardis_portal.storage_box.cache_files', u'id': u'8767709f-ae98-4735-9d29-21bb5b13e230', u'worker_pid': 15906}
  
Notice that most tasks have the default priority of 5 (defined in
``tardis/default_settings/celery_settings.py`` as ``DEFAULT_TASK_PRIORITY`` and
that the task operating on a file from the ``big-data1`` storage boxes has a lower priority of 4.

Default priorities for storage boxes can be configured via StorageBox Attributes.
We can check which storage boxes have priorites specified in the Django shell as follows::

  (mytardis) mytardis@celery0:~/mytardis$ ./manage.py shell_plus

  >>> StorageBoxAttribute.objects.filter(key='priority')
  <QuerySet [<StorageBoxAttribute: big-data1-> priority: 4>, <StorageBoxAttribute: big-data2-> priority: 4>]>

So in the example above, explicit priorities are only set for the "big-data1" and "big-data2" storage boxes.


Common Problems and Solutions
-----------------------------

Celery workers time out when running celery inspect active
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When running ``celery inspect active`` sometimes you will see this error::

  Error: No nodes replied within time constraint.

Usually, running ``celery inspect active`` again will resolve the problem,
i.e. it will just work without error on subsequent attempts.

If desired, you can specify a ``timeout`` e.g. ``timeout 10`` but usually
running ``celery inspect active`` again does the trick.


Non-priority queue already exists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If an attempt to submit a task to the queue (with ``apply_async`` triggers an error like this::

  PreconditionFailed: Queue.declare: (406) PRECONDITION_FAILED - inequivalent arg 'x-max-priority' for queue 'celery' in vhost '/':
   received the value '10' of type 'signedint' but current is none

This means that the MyTardis process attempting to submit the task is expecting
the queue to have the ``x-max-priority`` argument, but it doesn't have that
argument (see ``rabbitmqctl report`` above).

In this case, you can delete the ``celery`` queue, and allow Celery to recreate
it with the ``x-max-priority`` argument::

  (mytardis) mytardis@celery0 ~/mytardis$ DJANGO_SETTINGS_MODULE=tardis.settings celery -A tardis.celery.tardis_app amqp queue.delete celery

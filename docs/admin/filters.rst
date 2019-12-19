.. _ref-filterframework:

Filter Setup
============

With the ``USE_FILTERS`` option set to True in settings,
filters will be called once a file object has been verified.

Filters allow post-processing of uploaded files and can be used to extract
metadata from file headers and/or generate thumbnail images.

The DataFileObject's verify method submits a task called "mytardis.apply_filters"
to the message broker (RabbitMQ).

This task can be picked up by the "mytardis-filters" microservice:
https://github.com/mytardis/mytardis-filters or by your own custom microservice.
